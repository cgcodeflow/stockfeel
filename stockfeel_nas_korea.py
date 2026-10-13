"""Korean market adapter shared by desktop and NAS. No separate settings."""
import copy
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yfinance as yf

FUNDS = {'kospi200': ('코스피 200', '2ETF01', '069500', '.KS'),
         'kosdaq150': ('코스닥 150', '2ETF54', '229200', '.KQ')}
ORIGIN = 'https://www.samsungfund.com'
NOTE = '구성종목은 KODEX 200·KODEX 코스닥150의 국내 주식 보유목록을 사용합니다. 실제 지수 편입종목과 차이가 있을 수 있습니다.'


def get_json(url):
    response = requests.get(url, timeout=25, headers={'User-Agent': 'Stockfeel/1.0 Mozilla/5.0'})
    response.raise_for_status()
    return response.json()


def holdings(payload, suffix, expected):
    pdf = payload['pdf']
    if len(pdf['list']) != int(pdf['totalCnt']):
        raise ValueError('보유종목 전체 목록이 아닙니다')
    rows = {}
    for item in pdf['list']:
        code = str(item['itmNo'])
        # Cash, derivatives and other funds are not individual equity constituents.
        if not re.fullmatch(r'[0-9A-Z]{6}', code) or re.search(r'KODEX|TIGER|ETF|선물', item['secNm'], re.I):
            continue
        rows[code] = {'symbol': code + suffix, 'code': code, 'name': item['secNm'],
                      'sector': '기타', 'industry': '', 'sector_source': '분류 확인 중'}
    if not expected * .9 <= len(rows) <= expected * 1.1:
        raise ValueError('ETF 주식 목록 수가 예상 범위를 벗어났습니다')
    return list(rows.values()), pdf['gijunYMD']


def cap_won(value):
    text = str(value).replace(',', '').replace(' ', '').replace('원', '')
    total = 0
    for unit, scale in [('조', 10**12), ('억', 10**8), ('만', 10**4)]:
        if unit in text:
            n, text = text.split(unit, 1)
            total += float(n) * scale
    return total + (float(text) if text else 0)


def index_bars(payload, now=None):
    now = now or datetime.now(ZoneInfo('Asia/Seoul'))
    cutoff = now.date() if (now.hour, now.minute) >= (15, 45) else now.date() - timedelta(days=1)
    result = {}
    for row in payload:
        day = datetime.strptime(row['GIJUN_YMD'], '%Y%m%d').date()
        price = float(row.get('JISU') or 0)
        if day <= cutoff and price > 0:
            result[day.isoformat()] = {'date': day.isoformat(), 'close': price}
    bars = [result[k] for k in sorted(result)]
    if len(bars) < 200:
        raise ValueError('지수 일별 이력 부족')
    return bars


def yahoo_index_bars(symbol, existing=None, now=None, include_live=False, market="kr"):
    """Combine daily history and dated regular-session quotes; optionally include the open session."""
    zone = 'Asia/Seoul' if market == 'kr' else 'America/New_York'
    now = now or datetime.now(ZoneInfo(zone))
    now = now.astimezone(ZoneInfo(zone))
    settled = (15, 45) if market == 'kr' else (16, 15)
    close_time = (15, 30) if market == 'kr' else (16, 0)
    cutoff = now.date() if include_live or (now.hour, now.minute) >= settled else now.date() - timedelta(days=1)
    ticker = yf.Ticker(symbol)
    frame = ticker.history(period='2y', auto_adjust=False, timeout=15)
    result = {b['date']: dict(b) for b in (existing or []) if b['date'] <= cutoff.isoformat()}
    if frame is not None and not frame.empty and 'Close' in frame:
        for stamp, value in frame['Close'].items():
            if pd.notna(value) and float(value) > 0 and stamp.date() <= cutoff:
                result[stamp.date().isoformat()] = {'date': stamp.date().isoformat(), 'close': float(value)}
    meta = ticker.get_history_metadata() or {}
    price, traded = meta.get('regularMarketPrice'), meta.get('regularMarketTime')
    if price and traded is not None:
        stamp = pd.Timestamp(traded, unit='s', tz='UTC') if isinstance(traded, (int, float)) else pd.Timestamp(traded)
        if stamp.tzinfo is None:
            stamp = stamp.tz_localize(meta.get('exchangeTimezoneName') or zone)
        stamp = stamp.tz_convert(zone)
        if stamp.date() <= cutoff and stamp <= now and (include_live or (stamp.hour, stamp.minute) >= close_time) and float(price) > 0:
            result[stamp.date().isoformat()] = {'date': stamp.date().isoformat(), 'close': float(price), 'quoted_at': stamp.isoformat()}
    bars = [result[k] for k in sorted(result)]
    if bars:
        bars[-1]['intraday'] = bool(include_live and bars[-1]['date'] == now.date().isoformat() and (now.hour, now.minute) < settled)
    if not bars:
        raise ValueError('Yahoo 지수 이력 없음: ' + symbol)
    return bars


def make_service(base, folder, config):
    # Using the running edition's calculator keeps both versions consistent.
    class KoreanStockfeel(base.Stockfeel):
        indexes = {key: (v[0], 'KR:' + key) for key, v in FUNDS.items()}
        currency = 'KRW'
        market = 'kr'
        seed_file = 'universe_kr.json'

        def get_universe(self):
            groups, dates = {}, {}
            for key, (_, fund, ticker, suffix) in FUNDS.items():
                product = get_json(f'{ORIGIN}/api/v1/kodex/product/{fund}.do')
                if product['info']['product']['stkTicker'] != ticker:
                    raise ValueError('ETF 코드 불일치')
                groups[key], dates[key] = holdings(product, suffix, 200 if key == 'kospi200' else 150)
            sector_names, _ = self.store.get('sector_names')
            sector_names = sector_names or {}
            try:
                cursor = ""
                for page in range(10):
                    obj = get_json('https://m.stock.naver.com/front-api/stock/sectors/all'
                                   '?nationType=domestic&sectorType=upjong&sectorSortType=CHANGE_RATE'
                                   f'&businessDayCategory=daily&pageSize=50&cursor={cursor}')
                    items = obj['result']['sectors']
                    sector_names.update({str(x['code']): x['name'] for x in items})
                    if not obj['result'].get('hasNext'):
                        break
                    next_cursor = obj['result'].get('cursor')
                    if not next_cursor or next_cursor == cursor:
                        raise ValueError('업종 목록 페이지 연결 오류')
                    cursor = next_cursor
                self.store.put('sector_names', sector_names)
            except Exception:
                base.LOG.exception('Korean sector directory delayed')
            previous = {r['symbol']: r for rows in (self.universe or {}).get('groups', {}).values() for r in rows}
            rows = [r for group in groups.values() for r in group]
            def metadata(row):
                obj = get_json(f'https://m.stock.naver.com/api/stock/{row["code"]}/integration')
                sector = sector_names.get(str(obj.get('industryCode')))
                cap = next((x['value'] for x in obj.get('totalInfos', []) if x['code'] == 'marketValue'), None)
                return row, sector, cap_won(cap) if cap else None
            self.set_status(stage='classification', total=len(rows), done=0, message='한국 업종 분류와 시가총액 확인 중')
            with ThreadPoolExecutor(max_workers=4) as pool:
                jobs = {pool.submit(metadata, row): row for row in rows}
                for done, future in enumerate(as_completed(jobs), 1):
                    row = jobs[future]
                    old = previous.get(row['symbol'], {})
                    for field in ('sector', 'industry', 'sector_source'):
                        if field in old:
                            row[field] = old[field]
                    try:
                        _, sector, cap = future.result()
                        if sector:
                            row.update(sector=sector, industry=sector, sector_source='Npay 공개 업종 분류')
                        if cap and cap > 0:
                            self.caps[row['symbol']] = {'value': cap, 'currency': 'KRW', 'issuer': row['symbol'],
                                                       'saved': time.time(), 'asof': base.utcnow()}
                    except Exception:
                        pass
                    if row['sector'] == '기타':
                        if row['code'] in ('005930', '000660'):
                            row.update(sector='반도체 · 삼성/하이닉스', sector_source='보완 분류')
                        else:
                            row['sector_source'] = '공개 업종 미확인'
                    self.set_status(done=done)
            self.store.put('market_caps', self.caps)
            return {'groups': groups, 'fetched_at': base.utcnow(), 'holding_dates': dates,
                    'sources': {key: f'{ORIGIN}/etf/product/view.do?id={v[1]}' for key, v in FUNDS.items()},
                    'note': NOTE}

        def view(self):
            result = super().view()
            result.update(market='kr', currency='KRW', universe_note=NOTE,
                          holding_dates=(self.universe or {}).get('holding_dates', {}))
            return result

        def collect(self):
            self.set_status(busy=True, stage='universe', done=0, total=0, errors=[], message='한국 구성종목 확인 중')
            warnings = []
            _, saved = self.store.get('universe')
            if not self.universe or time.time() - saved >= self.config['data']['universe_refresh_seconds']:
                try:
                    self.universe = self.get_universe()
                    self.store.put('universe', self.universe)
                except Exception:
                    if not self.universe:
                        seed = base.BASE / 'stockfeel_assets' / self.seed_file
                        if seed.exists():
                            self.universe = json.loads(seed.read_text(encoding='utf8'))
                    if not self.universe:
                        raise
                    warnings.append('한국 보유종목 갱신 지연: 마지막 저장 목록 사용')
            groups = self.universe['groups']
            stocks = sorted({r['symbol'] for rows in groups.values() for r in rows})
            data, missing = {}, []
            for key, (_, fund, _, _) in FUNDS.items():
                symbol = self.indexes[key][1]
                bars, saved = self.store.get('bars:' + symbol)
                try:
                    if not bars or time.time() - saved >= self.refresh_seconds:
                        # Preserve full historical data; Yahoo KS200 currently has sparse history.
                        try:
                            official = index_bars(get_json(f'{ORIGIN}/api/v1/kodex/product-earning/{fund}.do?srchTerm=12'))
                            merged = {b['date']: b for b in (official + (bars or []))}
                            bars = [merged[d] for d in sorted(merged)]
                        except Exception:
                            if not bars and key != 'kospi200':
                                raise
                        self.store.put('bars:' + symbol, bars)
                    if key == 'kospi200':
                        bars = yahoo_index_bars('^KS200', bars, include_live=True)
                        self.store.put('bars:' + symbol, bars)
                except Exception:
                    missing.append(symbol)
                    warnings.append(f'{self.indexes[key][0]} 지수 이력 갱신 지연')
                if bars:
                    data[symbol] = bars
            todo = []
            for symbol in stocks:
                bars, saved = self.store.get('bars:' + symbol)
                if bars:
                    data[symbol] = bars
                if not bars or time.time() - saved >= self.refresh_seconds:
                    todo.append(symbol)
            self.set_status(stage='prices', total=len(stocks), done=len(stocks)-len(todo), message='한국 종목 가격을 모으고 있어요')
            for offset in range(0, len(todo), 24):
                if self.stop.is_set():
                    return
                batch = todo[offset:offset+24]
                try:
                    frame = yf.download(batch, period='2y', auto_adjust=False, group_by='ticker',
                                        threads=4, progress=False, timeout=15)
                except Exception:
                    frame = pd.DataFrame()
                def read_equity(symbol):
                    sub = frame[symbol] if isinstance(frame.columns, pd.MultiIndex) else frame
                    return base.equity_bars(sub, symbol, market='kr')
                with ThreadPoolExecutor(max_workers=4) as pool:
                    jobs = {pool.submit(read_equity, symbol): symbol for symbol in batch}
                    for future in as_completed(jobs):
                        symbol = jobs[future]
                        try:
                            bars = future.result()
                            data[symbol] = bars
                            self.store.put('bars:' + symbol, bars)
                        except Exception:
                            missing.append(symbol)
                self.set_status(done=len(stocks)-len(todo)+min(offset+len(batch), len(todo)))
                self.publish(groups, data, missing, warnings, False)
                self.stop.wait(.4)
            # Compare with actual completed equity sessions, never a weekday-only calendar.
            stock_dates = [data[s][-1]['date'] for s in stocks if data.get(s)]
            latest = max(stock_dates) if stock_dates else None
            for key in FUNDS:
                symbol = self.indexes[key][1]
                if latest and data.get(symbol) and data[symbol][-1]['date'] < latest:
                    if symbol not in missing:
                        missing.append(symbol)
                    warnings.append(f'{self.indexes[key][0]} 지수 제공 지연: {data[symbol][-1]["date"]} (종목 기준 {latest})')
            cap_failed = self.collect_caps(stocks)
            if cap_failed:
                warnings.append(f"한국 시가총액 {cap_failed}종목 갱신 지연")
            self.publish(groups, data, missing, warnings, True)
            self.set_status(busy=False, stage='ready', errors=warnings+missing, message='한국 지수 제공 지연 · 이전 종가 유지' if any(s.startswith('KR:') for s in missing) else '한국 시세 수집 완료')

    return KoreanStockfeel(folder=Path(folder), config=config)


def attach(app, us, base):
    from flask import jsonify, request, send_file
    kr = make_service(base, us.store.path.parent / 'korea', us.config)
    app.extensions['stockfeel_kr'] = kr
    app.add_url_rule('/kr', 'korea_page', lambda: base.page_response())
    app.add_url_rule('/us', 'us_page', lambda: base.page_response())
    @app.get('/api/stockfeel/kr')
    def korea_snapshot():
        result = kr.view()
        result['markets'] = us.view()['markets']
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-store'
        return response
    @app.post('/api/stockfeel/kr/refresh')
    def korea_refresh():
        if request.headers.get('Origin') and request.headers['Origin'].rstrip('/') != request.host_url.rstrip('/'):
            return jsonify(error='다른 사이트에서는 갱신할 수 없습니다.'), 403
        return jsonify(accepted=kr.trigger())
    return kr
