"""Merge new TradingView daily bars into history.json.

Usage: python3 update_history.py <history.json> <tv_response.json>

<tv_response.json> is the saved output of the TradingView get_ohlcv call for
INDEX:BTCUSD, interval 1D. Accepts either format:
  - rows:    {"bars": [{"t": unix_seconds, "o":..,"h":..,"l":..,"c":..,"v":..}, ...]}
  - columns: {"bars": {"t": [...], "o": [...], "h": [...], "l": [...], "c": [...], "v": [...]}}
Bars dated today (UTC) or later are dropped: the current day's bar is still forming.
Overlapping dates are overwritten with the newer values.
Prints a JSON summary; exits non-zero if no closed bars were found.
"""
import datetime as dt
import json
import sys

hist_path, tv_path = sys.argv[1:3]

hist = json.load(open(hist_path))
tv = json.load(open(tv_path))['bars']

if isinstance(tv, dict):  # columns layout
    rows = [{'t': t, 'o': o, 'h': h, 'l': l, 'c': c}
            for t, o, h, l, c in zip(tv['t'], tv['o'], tv['h'], tv['l'], tv['c'])]
else:
    rows = tv

today_utc = dt.datetime.now(dt.timezone.utc).date()
new = {}
for b in rows:
    d = dt.datetime.fromtimestamp(b['t'], dt.timezone.utc).date()
    if d >= today_utc:
        continue  # still forming
    new[d.isoformat()] = {'date': d.isoformat(), 'o': float(b['o']), 'h': float(b['h']),
                          'l': float(b['l']), 'c': float(b['c'])}

if not new:
    print(json.dumps({'error': 'no closed bars in response'}))
    sys.exit(1)

by_date = {b['date']: b for b in hist['bars']}
before = len(by_date)
by_date.update(new)
hist['bars'] = [by_date[k] for k in sorted(by_date)]
hist['updated_utc'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
json.dump(hist, open(hist_path, 'w'), separators=(',', ':'))

print(json.dumps({
    'bars_in_response_closed': len(new),
    'added': len(by_date) - before,
    'first_new': min(new),
    'last_bar': hist['bars'][-1]['date'],
    'total_bars': len(hist['bars']),
}))
