"""Build the XC Bitcoin Monthly Returns page from history.json and template.html.

Usage: python3 build_page.py <history.json> <template.html> <logo_b64.txt> <out.html>

Rules:
- Monthly return = month-end close / prior month-end close - 1 (closes from daily bars).
- Only complete calendar months are included. A month is complete when the last
  closed daily bar falls on or after its last day.
- 2010 is shown from August only (the first month with a prior close in the data
  shown, per the agreed rule).
"""
import json
import sys
from datetime import date

import pandas as pd

hist_path, tpl_path, logo_path, out_path = sys.argv[1:5]

hist = json.load(open(hist_path))
df = pd.DataFrame(hist['bars'])
df['date'] = pd.to_datetime(df['date'])
df = df.drop_duplicates('date', keep='last').sort_values('date').set_index('date')
last_bar = df.index.max()

# Month-end closes from the last available bar in each month
me = df['c'].groupby(df.index.to_period('M')).last()
me.index = me.index.to_timestamp(how='end').normalize()
ret = me.pct_change()

# Keep complete months only: month end must be on or before the last closed bar
ret = ret[ret.index <= last_bar.normalize()]
# Show from August 2010 onward
ret = ret[ret.index >= pd.Timestamp('2010-08-01')]

data = {str(y): [None] * 12 for y in range(2010, ret.index.max().year + 1)}
for d, v in ret.items():
    data[str(d.year)][d.month - 1] = round(float(v), 6)

last_complete = ret.index.max()
last_year = last_complete.year
asof_label = last_complete.strftime('%B %Y')
asof_date = f"{last_bar.day} {last_bar.strftime('%B %Y')}"

html = open(tpl_path, encoding='utf-8').read()
html = html.replace('/*DATA*/', json.dumps(data))
html = html.replace('/*LASTYEAR*/', str(last_year))
html = html.replace('/*ASOFLABEL*/', asof_label)
html = html.replace('/*ASOFDATE*/', asof_date)
html = html.replace('/*LOGO*/', open(logo_path, encoding='utf-8').read().strip())
open(out_path, 'w', encoding='utf-8').write(html)

print(json.dumps({
    'built': out_path,
    'last_bar': str(last_bar.date()),
    'last_complete_month': asof_label,
    'complete_months': int(ret.count()),
    'years': f"{min(data)}-{max(data)}",
    'built_on': date.today().isoformat(),
}))
