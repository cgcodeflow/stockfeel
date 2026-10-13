/* Stock Feel language settings and editable English translations. */
window.StockfeelI18n=(()=>{
 let saved;try{saved=localStorage.getItem('stockfeelLanguage')}catch(e){}const explicit=new URLSearchParams(location.search).get('lang');if(['ko','en'].includes(explicit))saved=explicit;
 const browser=(navigator.languages?.[0]||navigator.language||'ko').toLowerCase();
 const lang=['ko','en'].includes(saved)?saved:browser.startsWith('ko')?'ko':'en';
 const locale=lang==='en'?'en-US':'ko-KR';
 const dictionary={
 "이 사이트의 자료는 참고자료이며, 단기/중기의 추세자료만 제공합니다. 시세는 데이터 제공처와 수집 주기에 따라 지연될 수 있습니다.": "This site is for reference and shows short- and medium-term price trends. Quotes may be delayed by the data provider and collection interval.",
 "기분 1 공포, 5 보통, 9 환희": "Mood: 1 fear, 5 neutral, 9 euphoria",
 "미국장": "US market",
 "한국장": "Korean market",
 "처음이라면 ↗": "Start here ↗",
 "폰트": "Font",
 "작게": "Small",
 "보통": "Neutral",
 "크게": "Large",
 "라이트": "Light",
 "다크": "Dark",
 "시장 선택": "Choose a market",
 "글자 크기": "Font size",
 "화면 테마": "Theme",
 "주요 지수와 달러 환율": "Major indices and USD/KRW",
 "지수별 단기와 중기 추세": "Short- and medium-term index trends",
 "지수별 업종 목록": "Sectors by index",
 "중단기, 시장의 기분은?": "How is the market feeling?",
 "이평선, 볼린저밴드, 크로스 등을 이해하기 힘든 나를 위해 만들었다.": "Market trends, without the technical jargon.",
 "추세가 읽기 어려운 나, 100달러로 추세를 느끼자.": "Make sense of market trends with a simple $100 comparison.",
 "추세가 읽기 어려운 나, 10만원로 추세를 느끼자.": "Make sense of market trends with a simple ₩100,000 comparison.",
 "최신 지수 · 종목 추세": "Latest index & stock trends",
 "다음 갱신 시간 확인 중": "Checking the next update",
 "데이터 연결 중": "Connecting…",
 "어떤 업종이 움직이고 있을까요?": "Which sectors are moving?",
 "표정에 마우스를 올리면 추세 설명이 나와요. 업종 이름을 누르면 종목을 볼 수 있어요.": "Hover over a face to read the trend. Select a sector to see its stocks.",
 "업종·종목 검색": "Search sectors and stocks",
 "⌕  업종, 종목명, 티커 검색": "⌕  Search sectors, names or tickers",
 "업종 정렬": "Sort sectors",
 "시가총액 순": "Market cap",
 "종목 많은 순": "Stock count",
 "1주 수익률 순": "1-week return",
 "가나다순": "Alphabetical",
 "같은 $100, 다른 흐름.": "Same $100, different trends.",
 "같은 10만원, 다른 흐름.": "Same ₩100,000, different trends.",
 "업종 수익률은 해당 지수 내 종목에 같은 금액을 나눠 투자한 기준이에요.": "Sector returns assume an equal investment in each eligible stock within the index.",
 "공포": "Fear",
 "불안": "Anxious",
 "우울": "Downbeat",
 "기대": "Hopeful",
 "기쁨": "Happy",
 "환희": "Euphoric",
 "극도의 공포": "Extreme fear",
 "극도의 환희·탐욕": "Extreme greed",
 "닫기 ×": "Close ×",
 "설명 닫기": "Close guide",
 "추세 설명 닫기": "Close trend details",
 "계산 기준 자세히 보기": "How the scores are calculated",
 "표정 두 개면, 흐름이 보여요.": "Two faces, two time horizons.",
 "단기": "Short term",
 "중기": "Medium term",
 "단기 · 1주": "Short term · 1 week",
 "중기 · 3개월": "Medium term · 3 months",
 "오늘": "Today",
 "평온": "Calm",
 "급등": "Surging",
 "급락": "Falling sharply",
 "나스닥 종합": "Nasdaq Composite",
 "나스닥 100": "Nasdaq 100",
 "코스피 200": "KOSPI 200",
 "코스닥 150": "KOSDAQ 150",
 "코스피": "KOSPI",
 "코스닥": "KOSDAQ",
 "달러/원": "USD/KRW",
 "한국 대표 대형주": "Korean large-cap stocks",
 "코스닥 대표 성장기업": "Leading KOSDAQ growth companies",
 "미국 대표 대형주": "US large-cap stocks",
 "나스닥 대표 비금융 기업": "Leading non-financial Nasdaq companies",
 "투자의 책임은 본인에게 있습니다.": "You are responsible for your investment decisions.",
 "이 사이트의 자료는 참고자료이며, 단기/중기의 추세자료만 제공합니다. 시장의 현재 가격은 최소 10분의 지연이 있습니다.": "This site is for reference and shows short- and medium-term price trends. Quotes are delayed by at least 10 minutes.",
 "장중 시세": "Intraday quote",
 "장중": "Intraday",
 "제공값": "Latest quote",
 "종가": "Close",
 "갱신 지연": "Update delayed",
 "갱신 지연 · 집계 제외": "Delayed · excluded",
 "조회 대기": "Waiting for data",
 "가격 확인 중": "Checking prices",
 "전체 구성종목 수집 예정": "Collecting the constituent list",
 "데이터 준비 중": "Preparing data",
 "가격 이력을 확인하고 있어요": "Checking price history",
 "시장의 흐름을 읽고 있어요": "Reading the market trend",
 "첫 수집에는 시간이 걸릴 수 있어요. 이후에는 저장된 데이터로 빠르게 열려요.": "The first collection may take a while. Cached data makes later visits faster.",
 "데이터 부족": "Insufficient data",
 "이전 시세": "Previous quote",
 "동일금액 분산 기준": "Equal-weight allocation",
 "업종 / 집계 종목": "Sector / covered stocks",
 "검색 결과가 없어요. 다른 이름이나 티커를 입력해 주세요.": "No matches. Try another name or ticker.",
 "구성종목과 가격을 준비하고 있어요.\n수집이 진행되면 업종별로 표시됩니다.": "Preparing constituents and quotes. Sectors will appear as data becomes available.",
 "정기 수집 중 · 완료 후 갱신 예정": "Collecting data · update pending",
 "갱신 예정 시간 경과 · 다음 확인 후 반영": "Update due · checking again soon",
 "서버 정기 수집 시작 예정 시각입니다. 수집 완료와 캐시 반영에는 시간이 더 걸릴 수 있습니다.": "Scheduled collection start. Collection and cache updates may take additional time.",
 "최초 데이터 수집 중": "Collecting initial data",
 "연결 확인 필요": "Connection unavailable",
 "상승 지속형": "Sustained uptrend",
 "하락 지속형": "Sustained downtrend",
 "상승 전환형": "Turning upward",
 "하락 전환형": "Turning downward",
 "상승 둔화형": "Uptrend slowing",
 "중기 상승·단기 보합": "Medium-term rise, short-term flat",
 "중기 하락·단기 보합": "Medium-term decline, short-term flat",
 "단기 상승형": "Short-term uptrend",
 "단기 하락형": "Short-term downtrend",
 "전체 보합형": "Broadly flat",
 "강한 상승 지속형": "Strong sustained uptrend",
 "강한 하락 지속형": "Strong sustained downtrend",
 "최근 1주와 3개월 모두 상승하고 있어요.": "Both the past week and three months are up.",
 "최근 1주와 3개월 모두 하락하고 있어요.": "Both the past week and three months are down.",
 "3개월간 하락했지만, 최근 1주는 반등하고 있어요.": "Down over three months, with a rebound in the past week.",
 "3개월간 상승했지만, 최근 1주는 하락하고 있어요.": "Up over three months, with a pullback in the past week.",
 "3개월 흐름은 상승이지만, 최근 1주는 쉬어가고 있어요.": "The three-month trend is up, while the past week is taking a pause.",
 "3개월간 상승한 뒤, 최근 1주는 큰 변화가 없어요.": "Up over three months, with little change in the past week.",
 "3개월간 하락한 뒤, 최근 1주는 큰 변화가 없어요.": "Down over three months, with little change in the past week.",
 "3개월은 큰 변화가 없고, 최근 1주는 상승하고 있어요.": "Little change over three months, with a rise in the past week.",
 "3개월은 큰 변화가 없고, 최근 1주는 하락하고 있어요.": "Little change over three months, with a decline in the past week.",
 "최근 1주와 3개월 모두 뚜렷한 방향이 없어요.": "Neither the past week nor three months shows a clear direction.",
 "충분한 가격 이력이 모이면 추세를 표시합니다.": "Trends appear once enough price history is available.",
 "52주 이력 및 공통 기준일 데이터 필요": "52-week history and a common date are required",
 "당일 변동 데이터 부족": "Daily-change data unavailable",
 "시가총액 수집 대기 · 순위 미확정": "Waiting for market caps · order pending",
 "시장를 조금 쉽게.": "Markets made a little simpler.",
 "시장을 조금 쉽게 느끼자.": "Feel the market, a little more simply.",
 "1주일 평균~3개월 평균에 해당하는 지수의 단기/중기 가격 추세를 표시하는 사이트 입니다. 실시간 매수/매도를 목표로 하지 않습니다.": "This site shows short- and medium-term index price trends over one week and three months. It is not designed for real-time trading.",
 "개인적인 목적으로 만든 비영리 페이지 입니다. 언제까지 운영될지는 확신할 수 없습니다.": "A personal, non-profit project. Continued availability is not guaranteed.",
 "투자의 책임은 각 투자자에게 있습니다.": "Each investor is responsible for their own investment decisions."
};
 const sectors={
 "반도체": "Semiconductors",
 "기술": "Technology",
 "커뮤니케이션": "Communication services",
 "경기소비재": "Consumer discretionary",
 "필수소비재": "Consumer staples",
 "헬스케어": "Health care",
 "금융": "Financials",
 "산업재": "Industrials",
 "에너지": "Energy",
 "유틸리티": "Utilities",
 "소재": "Materials",
 "부동산": "Real estate",
 "기타": "Other",
 "IT서비스": "IT services",
 "가구": "Furniture",
 "가스유틸리티": "Gas utilities",
 "가정용기기와용품": "Household appliances & products",
 "건강관리기술": "Health care technology",
 "건강관리업체및서비스": "Health care providers & services",
 "건강관리장비와용품": "Health care equipment & supplies",
 "건설": "Construction",
 "건축자재": "Building materials",
 "게임엔터테인먼트": "Gaming",
 "광고": "Advertising",
 "교육서비스": "Education services",
 "기계": "Machinery",
 "다각화된통신서비스": "Diversified telecom services",
 "담배": "Tobacco",
 "디스플레이장비및부품": "Display equipment & components",
 "디스플레이패널": "Display panels",
 "무선통신서비스": "Wireless telecom",
 "무역회사와판매업체": "Trading companies & distributors",
 "반도체와반도체장비": "Semiconductors & equipment",
 "방송과엔터테인먼트": "Media & entertainment",
 "백화점과일반상점": "Department & general stores",
 "복합기업": "Conglomerates",
 "복합유틸리티": "Multi-utilities",
 "비철금속": "Non-ferrous metals",
 "상업서비스와공급품": "Commercial services & supplies",
 "생명과학도구및서비스": "Life sciences tools & services",
 "생명보험": "Life insurance",
 "생물공학": "Biotechnology",
 "석유와가스": "Oil & gas",
 "섬유,의류,신발,호화품": "Textiles, apparel & luxury goods",
 "소프트웨어": "Software",
 "손해보험": "Property & casualty insurance",
 "식품": "Food products",
 "양방향미디어와서비스": "Interactive media & services",
 "에너지장비및서비스": "Energy equipment & services",
 "우주항공과국방": "Aerospace & defense",
 "은행": "Banks",
 "음료": "Beverages",
 "인터넷과카탈로그소매": "Online & catalog retail",
 "자동차": "Automobiles",
 "자동차부품": "Auto components",
 "전기유틸리티": "Electric utilities",
 "전기장비": "Electrical equipment",
 "전기제품": "Electrical products",
 "전자장비와기기": "Electronic equipment & instruments",
 "전자제품": "Consumer electronics",
 "제약": "Pharmaceuticals",
 "조선": "Shipbuilding",
 "증권": "Capital markets",
 "창업투자": "Venture capital",
 "철강": "Steel",
 "카드": "Credit cards",
 "통신장비": "Communications equipment",
 "포장재": "Packaging",
 "항공사": "Airlines",
 "항공화물운송과물류": "Air freight & logistics",
 "해운사": "Marine transport",
 "핸드셋": "Mobile devices",
 "호텔,레스토랑,레저": "Hotels, restaurants & leisure",
 "화장품": "Cosmetics",
 "화학": "Chemicals"
};
 const phrases=Object.entries({...dictionary,...sectors}).filter(([k])=>k.length>5).sort((a,b)=>b[0].length-a[0].length);
 function t(value){
  if(lang==='ko'||value==null)return value;
  let s=String(value),trim=s.trim();
  if(dictionary[trim]||sectors[trim])return s.replace(trim,dictionary[trim]||sectors[trim]);
  for(const [ko,en]of phrases)s=s.replaceAll(ko,en);
  s=s.replace(/1주 전 (\$100|10만원)을 투자했다면\?/g,'What if you invested $1 a week ago?').replace(/3개월 전 (\$100|10만원)을 투자했다면\?/g,'What if you invested $1 three months ago?');
  s=s.replace(/(\d+) \/ (\d+)종목 시세 확인/g,'$1 / $2 stocks covered').replace(/(\d+) \/ (\d+)종목 집계/g,'$1 / $2 stocks included').replace(/(\d+)종목/g,'$1 stocks');
  s=s.replace(/(\d+) \/ 9 단계 · ([\d.]+)점/g,'Level $1 / 9 · $2 points').replace(/(\d+)\/9단계 · ([\d.]+)점/g,'Level $1 / 9 · $2 points');
  s=s.replace(/52주 종가 고점 대비 ([+−\-\d.]+)%예요\./g,'$1% from the 52-week closing high.');
  s=s.replace(/1주 전/g,'1 week ago').replace(/3개월 전/g,'3 months ago').replace(/마지막 수집 /g,'Last collected ').replace(/다음 수집 /g,'Next collection ').replace(/([\d,]+)초 후/g,'in $1s');
  s=s.replace(/ 종가부터의 수익률/g,' closing-price return').replace(/ · 전 거래일\(([^)]+)\) 대비 /g,' · vs previous session ($1): ').replace(/ · ±([\d.]+)%부터 급등\/급락/g,' · surge/drop threshold: ±$1%');
  s=s.replace(/ · 기간 수익률 /g,' · period return ').replace(/ · ±([\d.]+)%부터 색상 강조/g,' · color threshold: ±$1%').replace(/([\d.]+)점/g,'$1 points').replace(/ 추세 설명/g,' trend details');
  s=s.replace(/ 업종/g,' sectors').replace(/업종 시가총액 합계 /g,'Combined sector market cap ').replace(/종목 시총 확인 · 동일 회사 복수 주식 중복 제외/g,'stocks with market caps · share classes deduplicated');
  for(const [ko,en]of Object.entries(dictionary).filter(([k])=>k.length<=5).sort((a,b)=>b[0].length-a[0].length))s=s.replaceAll(ko,en);
  return s.replaceAll('10만원','₩100,000').replace(/([\d.,]+)조원/g,'₩$1 trillion').replace(/([\d,]+)원/g,'₩$1').replaceAll('문의 :','Contact:');
 }
 function apply(root=document.body){
  if(lang!=='en'||!root)return;
  const translateNode=node=>{if(node.nodeType===3&&!['SCRIPT','STYLE'].includes(node.parentElement?.tagName)&&!node.parentElement?.closest('.stock-name strong,[data-language]')){const text=t(node.textContent);if(text!==node.textContent)node.textContent=text;}};
  translateNode(root);
  if(root.nodeType!==1)return;
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);while(walker.nextNode())translateNode(walker.currentNode);
  for(const e of [root,...root.querySelectorAll('[title],[aria-label],[placeholder]')])for(const attr of ['title','aria-label','placeholder'])if(e.hasAttribute(attr)&&!e.closest('.stock-name,[data-language]')){const text=t(e.getAttribute(attr));if(text!==e.getAttribute(attr))e.setAttribute(attr,text);}
 }
 function init(){
  document.documentElement.lang=lang;
  document.querySelectorAll('[data-language]').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.language===lang));b.onclick=()=>{try{localStorage.setItem('stockfeelLanguage',b.dataset.language);const url=new URL(location.href);url.searchParams.delete('lang');location.assign(url.href)}catch(e){const url=new URL(location.href);url.searchParams.set('lang',b.dataset.language);location.assign(url.href)}};});
  if(lang==='en'){
   document.title='Stock Feel — '+(location.pathname.startsWith('/kr')?'Korean market':'Market mood');
   const normal=document.querySelector('button[data-font-size="normal"]');if(normal?.tagName==='BUTTON')normal.textContent='Normal';
   for(const [id,text]of Object.entries({dailyGuide:'Today compares the latest quote with the previous session. Red indicates a gain and blue a loss; calm changes are gray.',trendGuide:'Short-term trends cover one week, and medium-term trends cover three months.',refreshGuide:'Quotes are collected periodically and may be delayed by CDN caching. This is not a streaming quote service.'})){const e=document.getElementById(id);if(e)e.textContent=text;}
   const paragraphs=document.querySelectorAll('#guide p:not([id])');
   const guideText=[
    'Short term covers the past week; medium term covers three months. The two faces can differ because the same stock can pause or reverse over a shorter period.',
    'Fear turns blue, neutral uses the character’s base skin color, and euphoria turns red. Level 1 is an exaggerated lifeless face, while level 9 shows exaggerated greed with dollar-sign eyes and a gold tooth.',
    'The value below “$100 a week ago” shows what that investment would be worth now. Red means a gain; blue means a loss. On the Korean market page, the starting amount is ₩100,000.',
    'Hover over or select a sector face for trend details. You can also use the Tab key. Select a sector name to expand its stocks.',
    'Mood is a score from 0 to 100, grouped into nine levels. It combines period returns, normal price volatility and distance from the 52-week closing high. It describes price movement, not investor sentiment or a trading recommendation.',
    'Sector faces use an equal-weight price series starting about a year ago. Each return comparison assumes a new equal investment at the stated start date. Calculations use current constituents, not historical index membership.',
    'Only stocks with prices on a common date and sufficient history enter sector calculations. Coverage counts are shown. Newly listed, missing or delayed stocks may be excluded; stocks without a full 52-week history show returns only.'
   ];
   paragraphs.forEach((p,i)=>{if(guideText[i])p.textContent=guideText[i]});
   const formula=document.querySelector('#guide .formula');if(formula)formula.textContent='Score = 50 + 40 × tanh(period return ÷ (1.5 × volatility scale)) + 10 × high-position factor';
   apply();
   new MutationObserver(records=>{for(const record of records){if(record.type==='childList')for(const node of record.addedNodes)apply(node);else apply(record.target);}}).observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['title','aria-label','placeholder']});
  }
 }
 return {lang,locale,t,init};
})();
