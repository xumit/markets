"""Build the Nifty monthly returns page from nifty_history.json and template.html.

Usage (from anywhere):
    python3 sp500-monthly-returns/build/nifty_build.py

Monthly return = month-end close / prior month-end close - 1 (Nifty 50 price index, points).
A month is included only when its last day is on or before the last closed bar, so the
current month is left out until it ends. Writes sp500-monthly-returns/index.html.
"""
import calendar
import json
import os
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'index.html')

hist = json.load(open(os.path.join(HERE, 'nifty_history.json')))
months = hist['months']
last_bar = max(dt.date.fromisoformat(m['last']) for m in months)

# Month-end closes in order; returns for complete months only
closes = [(m['month'], m['c']) for m in months]
ret = {}
for i in range(1, len(closes)):
    mon, c = closes[i]
    y, mo = int(mon[:4]), int(mon[5:7])
    month_end = dt.date(y, mo, calendar.monthrange(y, mo)[1])
    if month_end > last_bar:
        continue
    prev_c = closes[i - 1][1]
    ret[(y, mo)] = c / prev_c - 1

first_year = 1927
last_complete = max(ret)
last_year = last_complete[0]
data = {str(y): [None] * 12 for y in range(first_year, last_year + 1)}
for (y, mo), v in ret.items():
    if y >= first_year:
        data[str(y)][mo - 1] = round(v, 6)

MON_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
             'August', 'September', 'October', 'November', 'December']
asof_label = f"{MON_NAMES[last_complete[1] - 1]} {last_complete[0]}"
asof_date = asof_label  # monthly data: labelled by the last complete month
# Data through: last closed bar date, in words
lb = last_bar
asof_through = f"{lb.day} {lb.strftime('%B %Y')}"

html = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
html = (html.replace('/*DATA*/', json.dumps(data))
            .replace('/*LASTYEAR*/', str(last_year))
            .replace('/*ASOFLABEL*/', asof_label)
            .replace('/*ASOFDATE*/', asof_through)
            .replace('/*LOGO*/', open(os.path.join(HERE, 'logo_b64.txt')).read().strip()))
open(OUT, 'w', encoding='utf-8').write(html)
print(json.dumps({'built': os.path.normpath(OUT), 'last_closed_day': str(last_bar),
                  'last_complete_month': asof_label, 'months': len(ret)}))
