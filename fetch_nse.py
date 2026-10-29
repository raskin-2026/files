#!/usr/bin/env python3
"""Fetch weekly Nifty 50 valuation data from NSE and append it to data/weekly.json.

Run weekly (Fri after market close). Needs: pip install requests
Buffett indicator is NOT on NSE: set it in data/config.json (updated ~quarterly).
"""
import json, sys, time, datetime as dt
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
WEEKLY = ROOT / "weekly.json"
CONFIG = ROOT / "config.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/market-data/live-market-indices",
}

# ---- scoring: exact port of the page's JS ----
def pw(v, bp, sc):
    if v <= bp[0]: return sc[0]
    if v >= bp[-1]: return sc[-1]
    for i in range(len(bp) - 1):
        if bp[i] <= v <= bp[i + 1]:
            r = (v - bp[i]) / (bp[i + 1] - bp[i])
            return sc[i] + r * (sc[i + 1] - sc[i])
    return 50
cl = lambda v: max(0, min(100, v))
def score(pe, pb, dy, vix, buf):
    s_pe = cl(pw(pe, [16, 20, 22.5, 24.5, 27, 32], [2, 20, 45, 65, 80, 99]))
    s_pb = cl(pw(pb, [2.2, 3, 3.5, 3.9, 4.3, 4.9], [2, 20, 45, 65, 80, 99]))
    s_dy = cl(pw(dy, [.8, .95, 1.1, 1.25, 1.45, 1.9], [99, 80, 65, 45, 20, 2]))
    s_vx = cl(pw(vix, [10, 11.5, 12.5, 14, 18, 24], [92, 80, 65, 45, 20, 5]))
    s_bf = cl(pw(buf, [75, 95, 115, 135, 148, 165], [3, 20, 45, 65, 80, 98]))
    return round(s_pe*.40 + s_pb*.25 + s_dy*.15 + s_vx*.10 + s_bf*.10, 1)

def nse_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    for _ in range(3):                      # prime cookies; NSE rejects cookie-less calls
        try:
            s.get("https://www.nseindia.com", timeout=20)
            return s
        except requests.RequestException:
            time.sleep(3)
    sys.exit("Could not reach nseindia.com (blocked or down).")

def fetch(s):
    r = s.get("https://www.nseindia.com/api/allIndices", timeout=20)
    r.raise_for_status()
    rows = {d["index"]: d for d in r.json()["data"]}
    n, v = rows["NIFTY 50"], rows["INDIA VIX"]
    return dict(nifty=float(n["last"]), pe=float(n["pe"]), pb=float(n["pb"]),
                dy=float(n["dy"]), vix=float(v["last"]))

def main():
    cfg = json.loads(CONFIG.read_text()) if CONFIG.exists() else {"buffett": 132.0}
    log = json.loads(WEEKLY.read_text()) if WEEKLY.exists() else []
    d = fetch(nse_session())
    d["buffett"] = float(cfg["buffett"])
    d["date"] = dt.date.today().isoformat()
    d["score"] = score(d["pe"], d["pb"], d["dy"], d["vix"], d["buffett"])
    log = [x for x in log if x["date"] != d["date"]] + [d]
    log.sort(key=lambda x: x["date"])
    WEEKLY.write_text(json.dumps(log, indent=2))
    print("Saved:", d)

if __name__ == "__main__":
    main()
