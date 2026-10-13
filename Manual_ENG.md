# Stockfeel NAS

A browser dashboard for US and Korean market trends. Runs on Synology NAS, ordinary Linux, or Docker.

## Linux: quick start

Requires Python 3.10 or newer and an internet connection. Extract stockfeel_nas.zip, then run:

```bash
cd stockfeel_nas
python3 -m venv .venv
source .venv/bin/activate
pip install -r stockfeel_nas_requirements.txt
python3 stockfeel_nas.py
```

Open http://SERVER_IP:55557 in your browser. Keep the process running. Use Docker or a service manager for continuous operation.

## Required files

- stockfeel_nas.py: server
- stockfeel_nas_korea.py: Korean market adapter
- stockfeel_nas.ini: configuration
- stockfeel.html: dashboard
- bottom_title.html: editable footer
- stockfeel_assets/: mood images, translations and initial constituent lists
- stockfeel_nas_requirements.txt: Python dependencies

Direct Python execution creates the cache folder automatically. The process needs write permission. Synology may require the bind-mount source folder to exist before deployment; keep the supplied cache folder next to compose.nas.yaml.

## Configuration

Edit stockfeel_nas.ini, then restart the process or container. Comments are provided in Korean and English. Browser refresh alone does not reload settings.

| Option | Meaning | Shipped value |
| --- | --- | --- |
| display.mood_image | PNG filename in stockfeel_assets | frog-moods-v2.png |
| display.sector_trend | Sector trend: icon or score | icon |
| display.stock_trend | Stock trend: icon or score | score |
| display.show_stock_daily | Show daily stock badges | false |
| daily.index_threshold_pct | Index surge/drop threshold | 2% |
| daily.sector_threshold_pct | Sector surge/drop threshold | 2% |
| daily.stock_threshold_pct | Stock surge/drop threshold | 5% |
| score_color.short_threshold_pct | Color threshold for one-week return | 5% |
| score_color.medium_threshold_pct | Color threshold for three-month return | 15% |
| trend.week_neutral_pct | One-week flat range | +/-1% |
| trend.quarter_neutral_pct | Three-month flat range | +/-3% |
| trend.strong_week_pct | Strong one-week trend threshold | 5% |
| trend.strong_quarter_pct | Strong three-month trend threshold | 15% |
| data.refresh_seconds | Quote collection interval | 21600 seconds / six hours |
| data.universe_refresh_seconds | Constituent refresh | 86400 seconds / one day |
| data.market_cap_refresh_seconds | Market-cap refresh | 86400 seconds / one day |
| server.host | Listening address | 0.0.0.0 |
| server.port | Listening port | 55557 |
| server.threads | Web request worker threads | 4 |
| server.log_level | Logging level | INFO |
| storage.cache_dir | Persistent cache folder | stockfeel_nas_cache |

Enter positive percentages without the % sign. Relative cache paths are resolved from the INI file location. Absolute paths also work. Select a different INI with:

```bash
python3 stockfeel_nas.py --config /path/to/stockfeel_nas.ini
```

## Mood images

To use the original human character:

```ini
[display]
mood_image = meme-moods-v2.png
```

The frog image remains available as frog-moods-v2.png. Custom images should be square PNGs with nine equal cells in a 3x3 grid: levels 1-9 run left to right, top to bottom. Place the PNG in stockfeel_assets and enter only its filename. Restart after changing the INI.

## Language and font size

The initial language follows the browser: Korean for Korean browsers, English otherwise. A manual selection is remembered. Desktop defaults to Normal; screens up to 760px wide default to Small. Manual font choices are remembered. Titles retain their size. Other text uses the increments in the HTML: --font-small:0pt, --font-normal:2pt, --font-large:4pt.

## Pages and data

US market: /us. Korean market: /kr. APIs: /api/stockfeel and /api/stockfeel/kr. Asset URLs start with /stockfeel_assets/.

Collection runs independently of page visits. Available intraday quotes update daily changes, short-/medium-term scores and returns for indices, stocks and sectors. This is periodic collection, not streaming quotes. The browser checks every five minutes. Sectors use eligible stocks on a common date and are sorted by combined market capitalization.

Yahoo Finance supplies available market prices. Korean constituent lists use official KODEX 200 and KODEX KOSDAQ150 equity holdings, which may differ from actual index membership. Korean sectors use public Npay classifications. KOSPI200 combines official historical data with available Yahoo quotes. KOSDAQ150 index data may be delayed while its constituent stocks and sectors continue to update. Missing or delayed stocks may be excluded from sector aggregation. Mood scores describe price trends, not investor sentiment or trading recommendations.

## Editing and updating

With the supplied folder mounts, HTML, footer, translations and images can be edited without rebuilding. Refresh the browser afterward. Edit footer text in bottom_title.html.

Restart after Python or INI changes. Rebuild after dependency or Dockerfile changes. If an older deployment uses image-internal files only, apply the supplied Compose folder mounts once. Clear browser or external CDN caches as needed. The ordinary NAS API uses Cache-Control: no-store.

Keep stockfeel_nas_cache across updates. Stop the server before moving it. The database filename is stockfeel.sqlite3 at the cache root and in its korea subfolder.

The default setup is a local-network HTTP service with no login. Configure a separate HTTPS/authentication proxy if publishing it publicly.
