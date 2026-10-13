# stockfeel<br>

한국어는 "README_한글"을 참조해주세요<br>

A lightweight Python web server that scores major US and Korean stocks by their 1-week, 3-month, and drawdown-from-high volatility, and displays the results as intuitive mood icons.<br>
You can check what it does on https://stockfeel.net

<img width="1487" height="1137" alt="image" src="https://github.com/user-attachments/assets/1ea87219-1fa2-45e9-b22f-c0b09764d86d" />

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
Market data is fetched with [yfinance](https://github.com/ranaroussi/yfinance), an unofficial library that uses Yahoo Finance's publicly available data. Data fetching can be somewhat slow.<br>
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
