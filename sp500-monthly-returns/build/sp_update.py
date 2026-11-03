"""Merge new TradingView daily bars (TVC:SPX) into sp_history.json, then rebuild the page.

Usage (from the repository root):
    python3 sp500-monthly-returns/build/sp_update.py <tv_response.json>

<tv_response.json> is the saved TradingView get_ohlcv output for TVC:SPX, interval 1D.
It accepts the rows layout ({"bars": [{"t": unix_seconds, "c": close, ...}]}) or the
columns layout ({"bars": {"t": [...], "c": [...], ...}}).
Bars dated today (UTC) or later are dropped: today's bar is still forming.

Each calendar month keeps the close of its last closed bar, so the current month
updates daily and is finalised when the month ends. The builder shows complete
months only.
"""
import datetime as dt
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
HIST = os.path.join(HERE, 'sp_history.json')

tv_path = sys.argv[1]
hist = json.load(open(HIST))
tv = json.load(open(tv_path))['bars']
if isinstance(tv, dict):
    rows = [{'t': t, 'c': c} for t, c in zip(tv['t'], tv['c'])]
else:
    rows = tv

today_utc = dt.datetime.now(dt.timezone.utc).date()
latest = {}
for b in rows:
    d = dt.datetime.fromtimestamp(b['t'], dt.timezone.utc).date()
    if d >= today_utc:
        continue
    prev = latest.get(d.strftime('%Y-%m'))
    if prev is None or d.isoformat() >= prev['last']:
        latest[d.strftime('%Y-%m')] = {'c': float(b['c']), 'last': d.isoformat(), 'day': d}

if not latest:
    print(json.dumps({'error': 'no closed bars in response'}))
    sys.exit(1)

by_month = {m['month']: m for m in hist['months']}
added = 0
for month, rec in latest.items():
    old = by_month.get(month)
    if old is None or old['last'] <= rec['last']:
        if old is None:
            added += 1
        by_month[month] = {'month': month, 'c': rec['c'], 'last': rec['last'], 'source': 'tradingview'}
hist['months'] = [by_month[k] for k in sorted(by_month)]
hist['updated_utc'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
json.dump(hist, open(HIST, 'w'), separators=(',', ':'))

print(json.dumps({'months_updated': sorted(latest), 'new_months': added,
                  'last_closed_day': max(r['last'] for r in latest.values())}))

# Rebuild the page
subprocess.run([sys.executable, os.path.join(HERE, 'sp_build.py')], check=True)
