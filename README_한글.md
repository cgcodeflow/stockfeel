# stockfeel<br>

초보자와 시간이 없는 개미투자자들을 위해, 차트를 볼 필요없이 시장과 각섹터의 단기(1주), 중기(3개월) 투자성과 그리고 변동성을 기준으로 분위기를 시각화 하여 보여주는 파이썬 웹서버 툴 입니다.
<br>
어떤 기능인지는 우측 사이트에서 먼저 체크해 볼 수 있습니다 : https://stockfeel.net

## What it does
- Scores representative stocks in the **US** and **Korean** markets based on 1-week / 3-month price changes and distance from their recent high.<br>
- Shows the **mood of each sector** at a glance, so you can see how the trend has developed so far.<br>
- Shows the **Return on Investment** of a hypothetical $100 invested 1 week ago and 3 months ago, to help you read the overall market sentiment.<br>

## Supported markets<br>
- US stock market<br>
- Korean stock market (KOSPI 200 / KOSDAQ 150)<br>

## Tested on<br>
- Linux<br>
- Docker (container)<br>
- Windows (with Python)<br>

## Requirements<br>
- Python >= 3.12<br>
Install dependencies with: pip install -r requirements.txt<br>
    Flask>=3.0,<4<br>
    pandas>=2.2,<4<br>
    yfinance>=0.2.65,<2<br>
    lxml>=5,<7<br>
    requests>=2.32,<3<br>
    waitress>=3.0.2,<4<br>
    tzdata>=2024.1<br>

## Data source<br>
Market data is fetched with [yfinance](https://github.com/ranaroussi/yfinance),<br>, an unofficial library that uses Yahoo Finance's publicly available data. Data fetching can be somewhat slow.<br>
Since Yahoo Finance does not provide the KOSDAQ 150 index, Korean market data is built by fetching and updating each constituent stock individually.<br>

## Configuration
- Default settings are defined in the `.ini` file. Changes take effect after restarting the container or the Python process.<br>
- HTML templates are read on every request, so edits are reflected immediately without a restart.<br>

## Icon sets
- **Default:** `stockfeel_assests/meme-moods-v2.png`<br>
- **Frog set:** `frog-moods-v2.png` (not included)<br>
The frog icon set was generated with GPT image and may be considered an homage to Matt Furie's Pepe the Frog. It is therefore **not distributed** with this repository. To use your own frog icons, place a file named `frog-moods-v2.png` in the icons folder and select it in the `.ini` file.<br>

## Disclaimer<br>
This project is for personal and educational use only and is **not financial advice**. It is not affiliated with or endorsed by Yahoo. Please review Yahoo's terms of use before using the data.
