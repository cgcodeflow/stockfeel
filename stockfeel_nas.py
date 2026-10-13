#!/usr/bin/env python3
"""Stockfeel: cached S&P 500 / Nasdaq 100 trend dashboard. Python 3.10+."""
from __future__ import annotations

import argparse
import signal
import calendar
import configparser
import copy
import io
import json
import logging
import math
from pathlib import Path
import sqlite3
import sys
import threading
import time
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
import yfinance as yf
from flask import Flask, jsonify, send_file, send_from_directory, make_response

BASE = Path(__file__).resolve().parent
LOG = logging.getLogger('stockfeel')
MARKETS = {'^GSPC': 'S&P 500', '^IXIC': '나스닥 종합', '^KS11': '코스피',
           '^KQ11': '코스닥', 'KRW=X': '달러/원'}
INDEXES = {'sp500': ('S&P 500', '^GSPC'), 'nasdaq100': ('나스닥 100', '^NDX')}
SOURCES = {'sp500': 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
           'nasdaq100': 'https://en.wikipedia.org/wiki/List_of_NASDAQ-100_companies'}
SECTORS = {'Information Technology': '기술', 'Technology': '기술',
           'Communication Services': '커뮤니케이션', 'Telecommunications': '커뮤니케이션',
           'Consumer Discretionary': '경기소비재', 'Consumer Staples': '필수소비재',
           'Health Care': '헬스케어', 'Healthcare': '헬스케어', 'Financials': '금융',
           'Industrials': '산업재', 'Energy': '에너지', 'Utilities': '유틸리티',
           'Materials': '소재', 'Basic Materials': '소재', 'Real Estate': '부동산'}
MOODS = ['극도의 공포', '공포', '불안', '우울', '보통', '기대', '기쁨', '환희', '극도의 환희·탐욕']

DEFAULT_CONFIG = {
    'display': {'sector_trend': 'icon', 'stock_trend': 'score', 'show_stock_daily': False, 'mood_image': 'frog-moods-v2.png'},
    'daily': {'index_threshold_pct': 2.0, 'sector_threshold_pct': 2.0, 'stock_threshold_pct': 5.0},
    'score_color': {'short_threshold_pct': 5.0, 'medium_threshold_pct': 15.0},
    'trend': {'week_neutral_pct': 1.0, 'quarter_neutral_pct': 3.0,
              'strong_week_pct': 5.0, 'strong_quarter_pct': 15.0},
    'data': {'refresh_seconds': 21600, 'universe_refresh_seconds': 86400, 'market_cap_refresh_seconds': 86400},
    'server': {'host': '0.0.0.0', 'port': 55557, 'threads': 4, 'log_level': 'INFO'},
    'storage': {'cache_dir': 'stockfeel_nas_cache'},
}


def load_config(filename=BASE / 'stockfeel_nas.ini'):
    result = copy.deepcopy(DEFAULT_CONFIG)
    parser = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=(';', '#'))
    try:
        if Path(filename).exists():
            with open(filename, encoding='utf-8-sig') as stream:
                parser.read_file(stream)
        for section in parser.sections():
            if section not in result:
                raise ValueError(f'알 수 없는 섹션 [{section}]')
            for key in parser[section]:
                if key not in result[section]:
                    raise ValueError(f'알 수 없는 설정 [{section}] {key}')
                default = result[section][key]
                try:
                    if isinstance(default, bool):
                        value = parser.getboolean(section, key)
                    elif isinstance(default, int):
                        value = parser.getint(section, key)
                    elif isinstance(default, float):
                        value = parser.getfloat(section, key)
                    else:
                        value = parser.get(section, key).strip()
                        if section == 'display' and key in ('sector_trend', 'stock_trend'):
                            value = value.lower()
                    if section == 'display' and key in ('sector_trend', 'stock_trend') and value not in ('icon', 'score'):
                        raise ValueError('icon 또는 score 필요')
                    if key == 'mood_image':
                        if '/' in value or chr(92) in value or not value.lower().endswith('.png') or Path(value).name != value:
                            raise ValueError('stockfeel_assets 폴더의 PNG 파일명만 입력하세요')
                        if not (BASE / 'stockfeel_assets' / value).is_file():
                            raise ValueError('PNG 파일을 찾을 수 없습니다: ' + value)
                    if isinstance(default, float) and (not math.isfinite(value) or not 0 < value <= 100):
                        raise ValueError('0 초과 100 이하 필요')
                    if isinstance(default, str) and not value:
                        raise ValueError('빈 값은 사용할 수 없습니다')
                    if key == 'threads' and not 1 <= value <= 64:
                        raise ValueError('1~64 필요')
                    if key == 'log_level':
                        value = value.upper()
                        if value not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
                            raise ValueError('DEBUG/INFO/WARNING/ERROR/CRITICAL 필요')
                    if key == 'port' and not 1024 <= value <= 65535:
                        raise ValueError('1024~65535 필요')
                    if section == 'data' and not (300 if key == 'refresh_seconds' else 3600) <= value <= 2592000:
                        raise ValueError('갱신 간격 범위를 확인하세요 (최대 30일)')
                    result[section][key] = value
                except ValueError as exc:
                    raise ValueError(f'[{section}] {key}: {exc}') from exc
        for short, strong in [('week_neutral_pct', 'strong_week_pct'), ('quarter_neutral_pct', 'strong_quarter_pct')]:
            if result['trend'][strong] <= result['trend'][short]:
                raise ValueError(f'[trend] {strong}은 {short}보다 커야 합니다.')
    except (ValueError, OSError, configparser.Error) as exc:
        raise ValueError(f'{filename} 설정 오류: {exc}') from exc
    return result


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def months_before(day, months):
    n = day.year * 12 + day.month - 1 - months
    year, m = divmod(n, 12)
    return date(year, m + 1, min(day.day, calendar.monthrange(year, m + 1)[1]))


def finite(n):
    try:
        return float(n) if math.isfinite(float(n)) else None
    except (TypeError, ValueError):
        return None


def trend_text(week, quarter, drawdown, config=None):
    """Preserve stock_list.html's direction thresholds, use plain descriptive text."""
    if week is None or quarter is None:
        return {'title': '데이터 준비 중', 'detail': '1주·3개월 가격이 모이면 추세를 표시해요.'}
    cfg = (config or DEFAULT_CONFIG)['trend']
    w = 1 if week > cfg['week_neutral_pct'] else -1 if week < -cfg['week_neutral_pct'] else 0
    q = 1 if quarter > cfg['quarter_neutral_pct'] else -1 if quarter < -cfg['quarter_neutral_pct'] else 0
    texts = {(1, 1): ('상승 지속형', '최근 1주와 3개월 모두 상승하고 있어요.'),
             (-1, -1): ('하락 지속형', '최근 1주와 3개월 모두 하락하고 있어요.'),
             (1, -1): ('반등 시도형', '3개월간 하락했지만, 최근 1주는 회복하고 있어요.'),
             (-1, 1): ('상승 둔화형', '3개월 흐름은 상승이지만, 최근 1주는 쉬어가고 있어요.'),
             (0, 1): ('중기 상승·단기 보합', '3개월간 상승한 뒤, 최근 1주는 큰 변화가 없어요.'),
             (0, -1): ('중기 하락·단기 보합', '3개월간 하락한 뒤, 최근 1주는 큰 변화가 없어요.'),
             (1, 0): ('단기 상승형', '3개월 흐름은 보합이지만, 최근 1주는 오르고 있어요.'),
             (-1, 0): ('단기 하락형', '3개월 흐름은 보합이지만, 최근 1주는 내리고 있어요.'),
             (0, 0): ('전체 보합형', '최근 1주와 3개월 모두 뚜렷한 방향이 없어요.')}
    title, detail = texts[w, q]
    if week >= cfg['strong_week_pct'] and quarter >= cfg['strong_quarter_pct']:
        title = '강한 상승 지속형'
    elif week <= -cfg['strong_week_pct'] and quarter <= -cfg['strong_quarter_pct']:
        title = '강한 하락 지속형'
    if drawdown is not None:
        detail += f' 52주 종가 고점 대비 {drawdown:+.1f}%예요.'
    return {'title': title, 'detail': detail}


def mood(ret, drawdown, volatility, days):
    if ret is None or drawdown is None or volatility is None:
        return None
    # Signed momentum dominates. High proximity adds at most 10 points.
    scale = max(1.0 if days == 5 else 3.0, volatility * math.sqrt(days))
    momentum = math.tanh(ret / (scale * 1.5))
    high_position = max(-1.0, min(1.0, 1 + drawdown / 15))
    score = max(0, min(100, 50 + 40 * momentum + 10 * high_position))
    level = max(1, min(9, int(score * 9 / 100) + 1))
    return {'level': level, 'label': MOODS[level - 1], 'score': round(score, 1)}


def analyze(bars, config=None):
    if not bars:
        return None
    closes = pd.Series({b['date']: b['close'] for b in bars if finite(b.get('close')) and b['close'] > 0}).sort_index()
    if closes.empty:
        return None
    end = date.fromisoformat(closes.index[-1])
    price = float(closes.iloc[-1])
    def period(target):
        h = closes.loc[closes.index <= target.isoformat()]
        if h.empty or (target - date.fromisoformat(h.index[-1])).days > 7:
            return None
        pct = (price / float(h.iloc[-1]) - 1) * 100
        return {'percent': round(pct, 4), 'value': round(100 + pct, 2), 'date': h.index[-1]}
    day = period(date.fromisoformat(closes.index[-2])) if len(closes) > 1 else None
    week, quarter = period(end - timedelta(days=7)), period(months_before(end, 3))
    year = closes.loc[closes.index >= (end - timedelta(weeks=52)).isoformat()]
    dd = (price / float(year.max()) - 1) * 100
    # New listings must not be presented as having a full 52-week history.
    full_year = date.fromisoformat(closes.index[0]) <= end - timedelta(days=360)
    volatility = finite(closes.pct_change().tail(63).std() * 100) if len(closes) >= 21 else None
    w, q = week['percent'] if week else None, quarter['percent'] if quarter else None
    graph = closes.tail(64)
    return {'price': price, 'asof': end.isoformat(), 'day': day, 'week': week, 'quarter': quarter,
            'drawdown': round(dd, 2), 'full_year': full_year,
            'short': mood(w, dd, volatility, 5) if full_year else None,
            'medium': mood(q, dd, volatility, 63) if full_year else None,
            'trend': trend_text(w, q, dd if full_year else None, config),
            'graph': [round(float(v) / float(graph.iloc[0]) * 100, 3) for v in graph],
            'intraday': bool(bars[-1].get('intraday')), 'quoted_at': bars[-1].get('quoted_at')}


class Store:
    """One SQLite connection per operation; readers never use a worker's connection."""
    def __init__(self, folder):
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / 'stockfeel.sqlite3'
        with closing(sqlite3.connect(self.path)) as con:
            con.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, payload TEXT NOT NULL, saved REAL NOT NULL)')
            con.commit()

    def get(self, key):
        with closing(sqlite3.connect(self.path, timeout=30)) as con:
            row = con.execute('SELECT payload,saved FROM cache WHERE key=?', (key,)).fetchone()
        return (json.loads(row[0]), row[1]) if row else (None, 0)

    def put(self, key, data):
        with closing(sqlite3.connect(self.path, timeout=30)) as con:
            con.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)', (key, json.dumps(data, ensure_ascii=False, allow_nan=False), time.time()))
            con.commit()


def get_universe():
    session = requests.Session()
    session.headers['User-Agent'] = 'Stockfeel/1.0 (personal market dashboard) Mozilla/5.0'
    groups = {}
    for key, url in SOURCES.items():
        response = session.get(url, timeout=30)
        response.raise_for_status()
        tables = pd.read_html(io.StringIO(response.text))
        table = next(t for t in tables if ('Symbol' in t.columns or 'Ticker' in t.columns) and
                     ('Security' in t.columns or 'Company' in t.columns) and len(t) > (400 if key == 'sp500' else 80))
        symbol_col = 'Symbol' if 'Symbol' in table else 'Ticker'
        name_col = 'Security' if 'Security' in table else 'Company'
        sector_col = next((c for c in table if 'Sector' in str(c) or str(c).startswith('ICB Industry')), None)
        industry_col = next((c for c in table if 'Sub-Industry' in str(c) or 'Subsector' in str(c)), None)
        rows = []
        for _, row in table.iterrows():
            symbol = str(row[symbol_col]).strip().replace('.', '-')
            raw_sector = str(row[sector_col]) if sector_col else ''
            industry = str(row[industry_col]) if industry_col else ''
            sector = '반도체' if 'semiconductor' in industry.lower() else SECTORS.get(raw_sector, '기타')
            rows.append({'symbol': symbol, 'name': str(row[name_col]), 'sector': sector, 'industry': industry})
        if not (450 <= len(rows) <= 550 if key == 'sp500' else 90 <= len(rows) <= 120):
            raise ValueError(f'{key}: 구성종목 수가 예상 범위를 벗어났습니다.')
        groups[key] = rows
    sp = {r['symbol']: r for r in groups['sp500']}
    for row in groups['nasdaq100']:
        if row['symbol'] in sp:
            row['sector'] = sp[row['symbol']]['sector']
            row['industry'] = sp[row['symbol']]['industry']
    return {'groups': groups, 'fetched_at': utcnow(), 'sources': SOURCES}


def frame_bars(frame, completed=True, market="us"):
    if frame is None or frame.empty or 'Close' not in frame:
        return []
    now = datetime.now(ZoneInfo('Asia/Seoul' if market == 'kr' else 'America/New_York'))
    # US daily candles are final only after regular close plus a short settlement margin.
    cutoff = now.date() if (now.hour, now.minute) >= ((15, 45) if market == 'kr' else (16, 15)) else now.date() - timedelta(days=1)
    result = {}
    for stamp, value in frame['Close'].items():
        val = finite(value)
        day = stamp.date()
        if val and val > 0 and day <= now.date() and (not completed or day <= cutoff):
            result[day.isoformat()] = {'date': day.isoformat(), 'close': val}
    return [result[k] for k in sorted(result)]


def equity_bars(frame, symbol, market='us', now=None):
    """Adjusted history including today's available price, without duplicating the session."""
    now = now or datetime.now(ZoneInfo('Asia/Seoul' if market == 'kr' else 'America/New_York'))
    def adjusted(source):
        if source is None or source.empty:
            return []
        adjusted_frame = source.copy()
        if 'Adj Close' in source:
            adjusted_frame['Close'] = source['Adj Close']
        return frame_bars(adjusted_frame, completed=False, market=market)
    bars = adjusted(frame)
    dated = {b['date']: b for b in bars}
    last_row = frame.index.max().date().isoformat() if frame is not None and not frame.empty else None
    # Yahoo sometimes supplies an empty current-day candle but a valid dated quote.
    if last_row and last_row <= now.date().isoformat() and (not bars or last_row > bars[-1]['date']):
        try:
            ticker = yf.Ticker(symbol)
            recent = ticker.history(period='5d', auto_adjust=False, timeout=10)
            dated.update({b['date']: b for b in adjusted(recent)})
            meta = ticker.get_history_metadata() or {}
            price, traded = finite(meta.get('regularMarketPrice')), meta.get('regularMarketTime')
            if price and price > 0 and traded is not None:
                stamp = pd.Timestamp(traded, unit='s', tz='UTC') if isinstance(traded, (int, float)) else pd.Timestamp(traded)
                zone = 'Asia/Seoul' if market == 'kr' else 'America/New_York'
                if stamp.tzinfo is None:
                    stamp = stamp.tz_localize(meta.get('exchangeTimezoneName') or zone)
                stamp = stamp.tz_convert(zone)
                day = stamp.date().isoformat()
                # Latest quote is unadjusted: it is on the current endpoint of Yahoo's adjusted series.
                if stamp <= now and day >= last_row:
                    dated[day] = {'date': day, 'close': price, 'quoted_at': stamp.isoformat()}
        except Exception:
            LOG.warning('Current equity candle delayed: %s', symbol)
    bars = [dated[d] for d in sorted(dated)]
    if not bars:
        raise ValueError('empty equity history: ' + symbol)
    if last_row and last_row <= now.date().isoformat() and bars[-1]['date'] < last_row:
        raise ValueError('latest equity candle unavailable: ' + symbol)
    settled = (15, 45) if market == 'kr' else (16, 15)
    bars[-1]['intraday'] = bars[-1]['date'] == now.date().isoformat() and (now.hour, now.minute) < settled
    return bars


def sector_cap(members, caps, currency="USD"):
    """Yahoo reports company market cap: count dual-class issuers only once."""
    issuers = {}
    covered = 0
    for member in members:
        item = caps.get(member['symbol'], {})
        value = finite(item.get('value'))
        if value is None or value <= 0 or item.get('currency') != currency:
            continue
        covered += 1
        issuer = item.get('issuer') or member['symbol']
        issuers[issuer] = max(issuers.get(issuer, 0), value)
    return (sum(issuers.values()) if issuers else None), covered


def cap_sort_key(sector):
    return (sector.get('market_cap') is None, -(sector.get('market_cap') or 0), sector['name'])


class Stockfeel:
    indexes = INDEXES
    currency = "USD"
    market = "us"
    seed_file = "universe.json"

    def get_universe(self):
        return get_universe()

    def __init__(self, folder=BASE / 'stockfeel_nas_cache', refresh_seconds=None, config=None):
        self.config = copy.deepcopy(config if config is not None else load_config())
        self.store = Store(folder)
        self.caps, _ = self.store.get('market_caps')
        self.caps = self.caps or {}
        self.refresh_seconds = max(300, refresh_seconds if refresh_seconds is not None else self.config['data']['refresh_seconds'])
        self.lock = threading.RLock()
        self.wake = threading.Event()
        self.stop = threading.Event()
        self.universe, _ = self.store.get('universe')
        self.snapshot, _ = self.store.get('snapshot')
        self.snapshot = self.snapshot or {'indices': [], 'markets': [], 'updated_at': None}
        self.status = {'busy': False, 'stage': 'ready', 'done': 0, 'total': 0, 'errors': [], 'message': '저장된 데이터 확인 중'}
        self.last_trigger = 0.0
        self.collection_lock = threading.Lock()
        self.next_collection_at = utcnow()
        # Recalculate cached descriptions with this run's settings before serving them.
        if self.universe and self.snapshot.get('indices'):
            symbols = {r['symbol'] for rows in self.universe['groups'].values() for r in rows}
            symbols.update(v[1] for v in self.indexes.values())
            cached = {s: self.store.get('bars:' + s)[0] for s in symbols}
            if any(cached.values()):
                self.publish(self.universe['groups'], {s: b for s, b in cached.items() if b},
                             self.snapshot.get('failed_symbols', []), self.snapshot.get('warnings', []), False)

    def set_status(self, **kwargs):
        with self.lock:
            self.status.update(kwargs)

    def view(self):
        with self.lock:
            data = copy.deepcopy(self.snapshot)
            data['status'] = copy.deepcopy(self.status)
            data['next_collection_at'] = self.next_collection_at
        data['served_at'] = utcnow()
        data['client_poll_seconds'] = 300
        data['edge_cache_seconds'] = 0
        data['refresh_seconds'] = self.refresh_seconds
        data['config'] = {k: copy.deepcopy(self.config[k]) for k in ('display', 'daily', 'score_color', 'trend')}
        return data

    def trigger(self):
        with self.lock:
            if self.status['busy'] or time.monotonic() - self.last_trigger < 60:
                return False
            self.last_trigger = time.monotonic()
            self.wake.set()
            return True

    def start(self):
        threading.Thread(target=self.loop, name='stockfeel-collector', daemon=True).start()

    def loop(self):
        while not self.stop.is_set():
            self.wake.clear()
            self.set_status(stage='queued', message='정기 수집 준비 중')
            # Serialize US/Korea collection to reduce peak load during NAS file transfers.
            with self.collection_lock:
                if self.stop.is_set():
                    return
                self.set_status(busy=True)
                with self.lock:
                    self.next_collection_at = None
                try:
                    self.collect()
                except Exception as exc:
                    LOG.exception('Collection failed')
                    self.set_status(busy=False, stage='error', message='데이터 연결을 확인해 주세요. 마지막 정상 데이터를 유지합니다.', errors=[str(exc)[:250]])
                interval = self.refresh_seconds if self.universe else 300
                with self.lock:
                    self.next_collection_at = (datetime.now(timezone.utc) + timedelta(seconds=interval)).isoformat(timespec='seconds')
            self.wake.wait(interval)

    def collect(self):
        self.set_status(busy=True, stage='universe', done=0, total=0, errors=[], message='지수 구성종목 확인 중')
        warnings = []
        _, saved = self.store.get('universe')
        if not self.universe or time.time() - saved > self.config['data']['universe_refresh_seconds']:
            try:
                self.universe = self.get_universe()
                self.store.put('universe', self.universe)
            except Exception as exc:
                if not self.universe:
                    seed = BASE / 'stockfeel_assets' / self.seed_file
                    if seed.exists():
                        self.universe = json.loads(seed.read_text(encoding='utf-8'))
                if not self.universe:
                    raise RuntimeError('구성종목 목록을 받지 못했습니다. 인터넷 연결 후 다시 시도해 주세요.') from exc
                warnings.append('구성종목 갱신 실패: 마지막 저장 목록을 사용합니다.')
        groups = self.universe['groups']
        stocks = sorted({r['symbol'] for rows in groups.values() for r in rows})
        symbols = list(dict.fromkeys([v[1] for v in self.indexes.values()] + stocks))
        data, missing, todo = {}, [], []
        for symbol in symbols:
            bars, saved = self.store.get('bars:' + symbol)
            if bars:
                data[symbol] = bars
            if not bars or time.time() - saved >= self.refresh_seconds:
                todo.append(symbol)
        self.set_status(stage='prices', total=len(symbols), done=len(symbols) - len(todo), message='종목별 가격을 모으고 있어요')
        for offset in range(0, len(todo), 24):
            if self.stop.is_set():
                return
            batch = todo[offset:offset + 24]
            try:
                frame = yf.download(batch, period='2y', interval='1d', auto_adjust=False,
                                    actions=False, group_by='ticker', threads=4, progress=False, timeout=15)
            except Exception:
                LOG.exception('Batch failed')
                frame = pd.DataFrame()
            def read_equity(symbol):
                sub = frame[symbol] if isinstance(frame.columns, pd.MultiIndex) else frame
                return equity_bars(sub, symbol, market=self.market)
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
            self.set_status(done=len(symbols) - len(todo) + min(offset + len(batch), len(todo)))
            if offset == 0 or offset % 96 == 0:
                self.publish(groups, data, missing, warnings, complete=False)
            if offset + 24 < len(todo):
                self.stop.wait(0.4)
        # Retry only failed tickers once, with bounded requests. The next cycle retries the rest.
        for symbol in missing[:12]:
            try:
                bars = equity_bars(yf.Ticker(symbol).history(period='2y', auto_adjust=False, timeout=10), symbol, market=self.market)
                if bars:
                    data[symbol] = bars
                    self.store.put('bars:' + symbol, bars)
                    missing = [s for s in missing if s != symbol]
            except Exception:
                pass
        # Index cards include available regular-session quotes on every collection.
        from stockfeel_nas_korea import yahoo_index_bars
        for _, symbol in self.indexes.values():
            try:
                data[symbol] = yahoo_index_bars(symbol, data.get(symbol), include_live=True, market=self.market)
                self.store.put('bars:' + symbol, data[symbol])
                missing = [s for s in missing if s != symbol]
            except Exception:
                if symbol not in missing:
                    missing.append(symbol)
                LOG.exception('Index quote delayed: %s', symbol)
        self.set_status(stage='markets', message='상단 지수·환율 갱신 중')
        markets = []
        old_markets = {r['symbol']: r for r in self.snapshot.get('markets', [])}
        for symbol, name in MARKETS.items():
            try:
                if symbol == '^GSPC' and data.get(symbol):
                    bars = data[symbol]
                elif symbol != 'KRW=X':
                    bars = yahoo_index_bars(symbol, include_live=True, market='kr' if symbol in ('^KS11', '^KQ11') else 'us')
                else:
                    h = yf.Ticker(symbol).history(period='1mo', auto_adjust=False, timeout=10)
                    bars = frame_bars(h, completed=False)
                if len(bars) < 2:
                    raise ValueError('insufficient history')
                markets.append({'symbol': symbol, 'name': name, 'price': bars[-1]['close'], 'asof': bars[-1]['date'],
                                'change': (bars[-1]['close'] / bars[-2]['close'] - 1) * 100,
                                'graph': [b['close'] for b in bars[-22:]], 'stale': False, 'intraday': bars[-1].get('intraday', False), 'quoted_at': bars[-1].get('quoted_at')})
            except Exception:
                markets.append({**old_markets.get(symbol, {'symbol': symbol, 'name': name}), 'stale': True})
        with self.lock:
            self.snapshot['markets'] = markets
        cap_failed = self.collect_caps(stocks)
        if cap_failed:
            warnings.append(f'시가총액 {cap_failed}종목 갱신 지연: 저장값 또는 일부 합계로 정렬합니다.')
        self.publish(groups, data, missing, warnings, complete=True)
        self.set_status(busy=False, stage='ready', done=len(symbols), total=len(symbols), errors=warnings + missing,
                        message='일부 시세는 이전 저장값입니다' if missing else '최신 수집 완료')

    def collect_caps(self, symbols):
        ttl = self.config['data']['market_cap_refresh_seconds']
        pending = [s for s in symbols if time.time() - self.caps.get(s, {}).get('saved', 0) >= ttl]
        if not pending:
            return 0
        self.set_status(stage='market_caps', message='업종 정렬용 시가총액 확인 중', done=0, total=len(pending))
        def fetch(symbol):
            info = yf.Ticker(symbol).get_info() or {}
            value = finite(info.get('marketCap'))
            if value is None or value <= 0 or info.get('currency') != self.currency:
                raise ValueError('USD 시가총액 없음')
            return {'value': value, 'currency': self.currency, 'issuer': (info.get('longName') or info.get('shortName') or symbol).strip().casefold(),
                    'saved': time.time(), 'asof': utcnow()}
        failed = 0
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix='market-cap') as pool:
            jobs = {pool.submit(fetch, symbol): symbol for symbol in pending}
            for done, future in enumerate(as_completed(jobs), 1):
                try:
                    self.caps[jobs[future]] = future.result()
                except Exception:
                    failed += 1
                self.set_status(done=done)
                if done % 24 == 0:
                    self.store.put('market_caps', self.caps)
        self.store.put('market_caps', self.caps)
        return failed

    def publish(self, groups, data, missing, warnings, complete):
        metrics = {s: analyze(bars, self.config) for s, bars in data.items()}
        indices = []
        for key, (name, symbol) in self.indexes.items():
            members = groups[key]
            target_date = (metrics.get(symbol) or {}).get('asof')
            if not target_date or self.market == 'kr' or (data.get(symbol) and data[symbol][-1].get('intraday')):
                dates = [metrics[r['symbol']]['asof'] for r in members if metrics.get(r['symbol'])]
                target_date = max(dates) if dates else None
            sectors = []
            for sector in sorted({r['sector'] for r in members}):
                rows = []
                series = []
                for member in (r for r in members if r['sector'] == sector):
                    m = metrics.get(member['symbol'])
                    current = bool(m and m['asof'] == target_date and member['symbol'] not in missing)
                    rows.append({**member, 'metrics': m, 'stale': not current, 'intraday': bool(m and m.get('intraday'))})
                    # Common-date equal-weight portfolio; no forward filling of stale quotes.
                    if current:
                        series.append(pd.Series({b['date']: b['close'] for b in data[member['symbol']]}))
                sector_metrics = None
                eligible = 0
                if series and target_date:
                    start = (date.fromisoformat(target_date) - timedelta(weeks=52)).isoformat()
                    qualified = [s for s in series if s.index.min() <= start]
                    eligible = len(qualified)
                    if qualified:
                        aligned = pd.concat(qualified, axis=1).dropna().sort_index()
                        # Include a small lead-in before 52 weeks for consistent history validation.
                        aligned = aligned.loc[aligned.index >= (date.fromisoformat(target_date) - timedelta(days=380)).isoformat()]
                        if not aligned.empty:
                            normalized = aligned.div(aligned.iloc[0]).mean(axis=1) * 100
                            portfolio = [{'date': d, 'close': float(v)} for d, v in normalized.items()]
                            sector_metrics = analyze(portfolio, self.config)
                            if sector_metrics:
                                sector_metrics['intraday'] = any(r['metrics'].get('intraday') for r in rows if r['metrics'] and not r['stale'])
                            # ROI uses a fresh equal-dollar investment at each requested start date.
                            if sector_metrics:
                                for period in ('day', 'week', 'quarter'):
                                    p = sector_metrics[period]
                                    if p:
                                        roi = float((aligned.iloc[-1] / aligned.loc[p['date']] - 1).mean() * 100)
                                        p.update(percent=round(roi, 4), value=round(100 + roi, 2))
                                w, q = sector_metrics['week'], sector_metrics['quarter']
                                sector_metrics['trend'] = trend_text(w['percent'] if w else None, q['percent'] if q else None, sector_metrics['drawdown'], self.config)
                market_cap, cap_covered = sector_cap(rows, self.caps, self.currency)
                sectors.append({'name': sector, 'count': len(rows), 'covered': eligible, 'metrics': sector_metrics,
                                'market_cap': market_cap, 'market_cap_covered': cap_covered, 'intraday': bool(sector_metrics and sector_metrics.get('intraday')),
                                'stocks': sorted(rows, key=lambda r: r['symbol'])})
            sectors.sort(key=cap_sort_key)
            indices.append({'key': key, 'name': name, 'symbol': symbol, 'count': len(members),
                            'covered': sum(bool(metrics.get(r['symbol']) and metrics[r['symbol']]['asof'] == target_date and r['symbol'] not in missing) for r in members),
                            'metrics': metrics.get(symbol), 'stale': symbol in missing, 'intraday': bool(data.get(symbol) and data[symbol][-1].get('intraday')), 'quoted_at': data[symbol][-1].get('quoted_at') if data.get(symbol) else None, 'sectors': sectors})
        with self.lock:
            markets = copy.deepcopy(self.snapshot.get('markets', []))
            # Keep the same S&P quote in both parts even during intermediate publishes.
            sp = metrics.get('^GSPC')
            if sp:
                for row in markets:
                    if row['symbol'] == '^GSPC':
                        row.update(price=sp['price'], asof=sp['asof'], change=(sp.get('day') or {}).get('percent'),
                                   intraday=bool(data['^GSPC'][-1].get('intraday')), stale='^GSPC' in missing)
            self.snapshot = {'indices': indices, 'markets': markets,
                             'updated_at': utcnow() if complete else self.snapshot.get('updated_at'),
                             'universe_date': self.universe['fetched_at'], 'sources': self.universe.get('sources', SOURCES),
                             'unique_count': len({r['symbol'] for rows in groups.values() for r in rows}),
                             'warnings': warnings, 'failed_symbols': missing}
            snap = copy.deepcopy(self.snapshot)
        if complete:
            self.store.put('snapshot', snap)


def page_response():
    """Read the editable footer on each page request; no restart needed for text edits."""
    page = (BASE / 'stockfeel.html').read_text(encoding='utf-8-sig')
    footer = (BASE / 'bottom_title.html').read_text(encoding='utf-8-sig')
    response = make_response(page.replace('<!-- STOCKFEEL_BOTTOM -->', footer))
    response.headers['Cache-Control'] = 'no-cache, max-age=0'
    return response


def create_app(service):
    app = Flask(__name__)
    @app.get('/')
    def index():
        return page_response()

    @app.get('/stockfeel_assets/<path:filename>')
    def assets(filename):
        return send_from_directory(BASE / 'stockfeel_assets', filename)

    @app.get('/api/stockfeel')
    def snapshot():
        response = jsonify(service.view())
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.post('/api/stockfeel/refresh')
    def refresh():
        from flask import request
        if request.headers.get('Origin') and request.headers['Origin'].rstrip('/') != request.host_url.rstrip('/'):
            return jsonify(error='다른 사이트에서는 갱신할 수 없습니다.'), 403
        return jsonify(accepted=service.trigger())
    from stockfeel_nas_korea import attach
    kr = attach(app, service, sys.modules[__name__])
    kr.collection_lock = service.collection_lock
    return app


def main():
    parser = argparse.ArgumentParser(description='Stockfeel NAS 서버 (Python 3.10+)')
    parser.add_argument('--config', type=Path, default=BASE / 'stockfeel_nas.ini',
                        help='NAS 설정 파일 경로')
    args = parser.parse_args()
    if not args.config.is_file():
        raise SystemExit(f'설정 파일이 없습니다: {args.config}')
    try:
        config = load_config(args.config)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    try:
        from waitress import serve
    except ImportError:
        raise SystemExit('필수 패키지를 설치하세요: pip install -r stockfeel_nas_requirements.txt')
    logging.basicConfig(level=config['server']['log_level'],
                        format='%(asctime)s %(levelname)s %(message)s')
    folder = Path(config['storage']['cache_dir']).expanduser()
    if not folder.is_absolute():
        folder = args.config.resolve().parent / folder
    service = Stockfeel(folder=folder, config=config)
    def shutdown(signum, frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, shutdown)
    app = create_app(service)
    service.start()
    app.extensions["stockfeel_kr"].start()
    try:
        serve(app, host=config['server']['host'],
              port=config['server']['port'], threads=config['server']['threads'])
    finally:
        app.extensions["stockfeel_kr"].stop.set()
        app.extensions["stockfeel_kr"].wake.set()
        service.stop.set()
        service.wake.set()


if __name__ == '__main__':
    main()
