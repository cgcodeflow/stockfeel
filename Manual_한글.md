# Stockfeel NAS

NAS 실행 파일과 INI는 독립적이며, 화면은 stockfeel.html, 이미지는 stockfeel_assets 폴더를 사용합니다.

## 설정
stockfeel_nas.ini 수정 후 프로세스/컨테이너를 재시작하세요.
- server.host: 0.0.0.0 (NAS IP로 접속)
- server.port: 55557
- server.threads: 웹 요청 처리 스레드 4개, 수집기는 하나
- server.log_level: INFO
- data.refresh_seconds: 시세 21600초(6시간)
- data.universe_refresh_seconds: 구성종목 86400초
- data.market_cap_refresh_seconds: 시가총액 86400초
- storage.cache_dir: INI 위치 기준 상대 경로 또는 절대 경로


## Python 직접 실행
Python 3.10 이상과 가상환경을 권장합니다.

    python -m pip install -r stockfeel_nas_requirements.txt
    python stockfeel_nas.py

다른 설정 파일: python stockfeel_nas.py --config /path/to/stockfeel_nas.ini
외부 HTTPS 연결과 캐시 폴더 쓰기 권한이 필요합니다. 최초 시작 시 수집하며 저장된 캐시가 있으면 먼저 제공합니다.

기본 구성은 내부망 HTTP용이며 로그인 기능은 없습니다. 인터넷 공개용 인증/HTTPS 프록시는 별도 구성해야 합니다. HTTPS 프록시 사용 시 수동 갱신 Origin 검증을 위한 프록시 헤더 설정도 검토해야 합니다.
시놀로지 모델/CPU의 Container Manager와 이미지 지원을 확인하세요. 실제 NAS/Docker 빌드는 이 환경에서 검증하지 않았습니다.


## 한국장 추가 파일
NAS 복사 시 stockfeel_nas_korea.py도 함께 복사하세요. Dockerfile.nas에 포함되어 있습니다. 미국장(/us)과 한국장(/kr)은 같은 stockfeel_nas.ini를 사용합니다. 한국 캐시도 연결된 캐시 폴더 아래 korea에 유지됩니다. stockfeel_assets/universe_kr.json은 공개 ETF 보유목록의 초기 저장본입니다. 실제 지수 목록과의 차이 및 데이터 출처는 화면과 README_ENG.md에 안내합니다.


## 캐시 폴더를 찾지 못하는 설치 오류
Container Manager가 폴더 연결을 먼저 검사할 수 있으므로 NAS 프로젝트 폴더에 stockfeel_nas_cache 폴더를 만들어 두세요. 예: /volume1/docker/stockfeel/stockfeel_nas_cache. 이 폴더는 compose.nas.yaml과 같은 위치에 있어야 합니다. 포함된 README.txt가 있는 폴더를 함께 복사해도 됩니다. Compose에는 누락된 호스트 폴더 자동 생성 옵션도 지정했습니다.
stockfeel_assets는 페페 이미지와 초기 구성목록이 들어 있는 필수 폴더입니다. 이름은 그대로 사용하며 stockfeel_nas_assets라는 별도 폴더는 필요하지 않습니다. 빈 assets 폴더만 만들면 이미지와 초기 목록이 없으므로 기존 폴더 내용을 모두 복사하세요.


## 하단 문구 수정
bottom_title.html은 실행 Python/메인 HTML과 같은 폴더에 두세요. 하단 안내와 stockfeel 문구를 이 파일에서 수정할 수 있습니다. UTF-8로 저장하고 페이지를 새로고침하면 적용되며, 서버 재시작은 필요하지 않습니다. data-template 안의 {unique_count}, {universe_date}는 종목 수와 구성 목록 날짜로 자동 치환됩니다. id="coverage"를 유지하면 자동 표시가 계속 동작합니다.
프로젝트 폴더의 bottom_title.html을 직접 수정하면 됩니다. 최신 Compose는 프로젝트 폴더 전체를 /app에 읽기 전용으로 연결합니다. Cloudflare 캐시가 있으면 해당 페이지(/, /us, /kr)의 캐시를 비우거나 만료까지 기다려야 합니다.


## HTML 수정 시 재빌드 없이 적용
최신 Compose는 프로젝트 폴더 전체를 /app에 읽기 전용으로 연결하고, 시세 캐시 폴더만 별도로 쓰기 가능하게 연결합니다. HTML, bottom_title.html, 이미지 수정은 NAS의 프로젝트 폴더에서 직접 하세요. 새로고침하면 적용됩니다. 편집기가 파일을 새 파일로 교체해 저장해도 폴더 연결이므로 바뀐 파일을 읽습니다.
Container Manager → 프로젝트 → 해당 프로젝트 → YAML 구성에서 최신 Compose 내용을 저장하고 변경된 구성으로 프로젝트를 배포하세요. 이 파일 연결 설정은 처음 한 번 적용해야 합니다. 이후 HTML 수정은 재빌드가 필요 없습니다. Python 코드 또는 INI를 바꾸면 컨테이너를 재시작하세요. requirements/Dockerfile 변경 시에는 이미지를 다시 빌드해야 합니다. Cloudflare/브라우저 캐시는 별도로 비워야 최신 HTML이 바로 보입니다.


## 글자 크기 조절
처음이라면과 라이트/다크 사이의 폰트 버튼으로 작게/보통/크게를 선택합니다. 처음에는 PC는 보통, 모바일(760px 이하)은 작게이며 선택은 브라우저에 저장됩니다. 제목은 고정하고 다른 글자에 보통 +2pt, 크게 +4pt를 적용합니다.
메인 HTML 상단 style의 --font-small:0pt; --font-normal:2pt; --font-large:4pt 값을 수정하면 증가량을 바꿀 수 있습니다. 예: 보통을 +3pt로 바꾸려면 --font-normal:3pt로 수정합니다. 1pt는 약 1.333px입니다. INI 수정이나 서버 재시작은 필요 없습니다. Cloudflare HTML 캐시는 비운 후 확인하세요.
종목명/티커 마우스 오버는 한국장 종목코드, 미국장 종목명만 표시합니다.


한국 지수 최신값 처리: 코스피(^KS11), 코스닥(^KQ11), 코스피200(^KS200)는 Yahoo Finance의 일봉과 거래 시각이 확인된 장 마감 시세를 함께 사용합니다. Yahoo 일봉 종가가 비어 있어도 검증된 마감 시세로 보완합니다. 코스피200의 과거 이력은 기존 공식 이력을 유지합니다. 코스닥150은 Yahoo의 조회 가능한 지수 티커가 확인되지 않아 삼성자산운용 기초지수를 유지하며, 종목 거래일보다 오래되면 지수 제공 지연으로 표시합니다.

지수 장중 반영: Yahoo의 최신 정규장 시세가 있으면 S&P500·나스닥100·코스피200 및 상단 종합지수에 반영하고, 지수 추세와 수익률도 같은 값으로 계산합니다. 장중에는 날짜 옆에 장중 시세를 표시합니다. S&P500 상하단은 같은 스냅샷 값을 사용합니다. 개별 종목·업종도 장중 시세가 있으면 해당 가격으로 계산합니다. 코스닥150은 조회 가능한 Yahoo 지수 티커가 확인되지 않아 기존 공식 이력 및 지연 표시를 유지합니다. 수집 및 화면 확인 주기, CDN 캐시 시간은 INI 설정을 따릅니다.


최신 화면·기능 반영: 한글/English 전환, 브라우저 언어 자동 선택, PC 보통·모바일 작게 기본 폰트, 수집·지연 알림 영역 제거, 미국·한국 종목 및 업종 장중 시세 계산을 제공합니다. 한국장 수집은 stockfeel_nas_korea.py에서 처리합니다. stockfeel_nas.ini와 기존 stockfeel_nas_cache를 유지하고, Python·HTML·bottom_title.html·stockfeel_assets 및 Dockerfile.nas를 최신 파일로 복사하세요. 기존 프로젝트의 전체 폴더 바인드 마운트를 사용한다면 파일 교체 후 컨테이너 재시작으로 적용됩니다. 이미지 내부 COPY만 사용하는 설치는 다시 빌드해야 합니다.


표정 이미지 선택: [display]의 mood_image = frog-moods-v2.png(기존 개구리) 또는 meme-moods-v2.png(새 사람형 9단계)로 설정합니다. PNG는 stockfeel_assets 폴더에 넣고 파일명만 지정하세요. 새 PNG는 같은 크기의 셀 3×3, 좌에서 우·위에서 아래 순서로 1~9단계가 배열된 정사각형 이미지를 사용하세요. INI 수정 후 컨테이너를 재시작하고, Cloudflare 버전은 두 API 캐시도 비워 설정을 즉시 반영하세요. 기존 설정 파일은 유지하면서 [display]에 mood_image 항목만 추가해도 됩니다.


이름 통일 배포: 실행 파일은 stockfeel_nas.py, 설정은 stockfeel_nas.ini, 한국장 모듈은 stockfeel_nas_korea.py, 화면은 stockfeel.html입니다. API는 /api/stockfeel 및 /api/stockfeel/kr, 이미지 URL은 /stockfeel_assets/ 입니다. 기존 NAS를 업데이트할 때는 새 Dockerfile.nas와 compose.nas.yaml로 프로젝트를 다시 빌드·배포하세요. 기존 시세 데이터를 유지하려면 이전 NAS 캐시 폴더를 stockfeel_nas_cache로 옮기고, 루트 및 korea 하위 폴더의 기존 SQLite 데이터 파일명을 stockfeel.sqlite3로 변경하세요. 서버를 정지한 상태에서 캐시를 이동하세요. 설정 수치는 새 이름의 INI로 유지하면 됩니다.
