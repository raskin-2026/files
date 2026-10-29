# Takapoisa weekly market mood site
- `index.html` – your calculator, now auto-loads `data/weekly.json`
- `scripts/fetch_nse.py` – pulls Nifty 50 PE/PB/DY + India VIX from NSE, scores it, appends a row
- `.github/workflows/weekly.yml` – runs it every Friday 5pm IST and commits the result
- `data/config.json` – Buffett indicator (manual, quarterly)

Deploy: push to GitHub, then Settings > Pages > deploy from main. Put `logo.jpeg` next to index.html.
Test locally: `pip install requests && python scripts/fetch_nse.py && python -m http.server`
