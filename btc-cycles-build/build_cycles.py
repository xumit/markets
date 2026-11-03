"""Build the Bitcoin bear, bull and halving-to-halving cycle pages from the shared price history.

Usage (from the repository root):
    python3 btc-cycles-build/build_cycles.py

Reads:  btc-monthly-returns/build/history.json   (daily closes, updated each day)
Writes: btc-bear-cycles/index.html
        btc-bull-cycles/index.html
        btc-halving-cycles/index.html

Cycle windows are the agreed ones. Ongoing cycles run to the last closed bar.
Prints one JSON line with the last bar date.
"""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
HIST = os.path.join(ROOT, 'btc-monthly-returns', 'build', 'history.json')

h = pd.DataFrame(json.load(open(HIST))['bars'])
h['date'] = pd.to_datetime(h['date'])
h = h.drop_duplicates('date', keep='last').set_index('date').sort_index()
last_bar = h.index.max()
asof = f"{last_bar.day} {last_bar.strftime('%B %Y')}"
logo = open(os.path.join(HERE, 'logo_b64.txt')).read().strip()


def cycle(name, start, end, status, extra=None):
    seg = h.loc[start:end, 'c']
    norm = seg / seg.iloc[0]
    d = {
        'name': name,
        'start': start,
        'end': str(seg.index[-1].date()) if status == 'Ongoing' else end,
        'status': status,
        'days': int(len(seg)),
        'startClose': round(float(seg.iloc[0]), 4),
        'endClose': round(float(seg.iloc[-1]), 2),
        'peakClose': round(float(seg.max()), 2),
        'peakDate': str(seg.idxmax().date()),
        'multiple': round(float(seg.max() / seg.iloc[0]), 2),
        'endMultiple': round(float(seg.iloc[-1] / seg.iloc[0]), 2),
        'series': [round(float(v), 6) for v in norm.values],
        'dates': [str(x.date()) for x in seg.index],
    }
    if extra:
        d.update(extra)
    return d


# ---- Bear cycles (all closed; agreed windows) ----
BEAR = [
    ('Bear Cycle 1', '2011-06-09', '2011-11-17'),
    ('Bear Cycle 2', '2013-11-30', '2015-01-14'),
    ('Bear Cycle 3', '2017-12-18', '2018-12-15'),
    ('Bear Cycle 4', '2021-11-11', '2022-11-21'),
    ('Bear Cycle 5', '2025-10-07', '2026-06-30'),
]
bear = []
for name, a, b in BEAR:
    c = cycle(name, a, b, 'Complete')
    seg = h.loc[a:b, 'c']
    trough_i = int(c['series'].index(min(c['series'])))
    c.update({
        'troughDay': trough_i + 1,
        'troughDate': str(seg.index[trough_i].date()),
        'troughX': float(min(c['series'])),
        'changePct': round((seg.iloc[-1] / seg.iloc[0] - 1) * 100, 1),
        'maxDdPct': round((seg.min() / seg.iloc[0] - 1) * 100, 1),
    })
    bear.append(c)

# ---- Bull cycles (agreed windows; Bull 6 ongoing) ----
BULL = [
    ('Bull Cycle 1', '2009-10-05', '2011-06-08', 'Complete'),
    ('Bull Cycle 2', '2011-11-18', '2013-11-29', 'Complete'),
    ('Bull Cycle 3', '2015-01-15', '2017-12-17', 'Complete'),
    ('Bull Cycle 4', '2018-12-16', '2021-11-10', 'Complete'),
    ('Bull Cycle 5', '2022-11-22', '2025-10-06', 'Complete'),
    ('Bull Cycle 6', '2026-07-01', str(last_bar.date()), 'Ongoing'),
]
bull = [cycle(n, a, b, s) for n, a, b, s in BULL]

# ---- Halving-to-halving cycles (Cycle 4 ongoing) ----
HALV = [
    ('H-H Cycle 1', '2012-11-28', '2016-07-09', 'Complete'),
    ('H-H Cycle 2', '2016-07-09', '2020-05-11', 'Complete'),
    ('H-H Cycle 3', '2020-05-11', '2024-04-20', 'Complete'),
    ('H-H Cycle 4', '2024-04-20', str(last_bar.date()), 'Ongoing'),
]
halv = [cycle(n, a, b, s) for n, a, b, s in HALV]


def write(template, data, out):
    html = open(os.path.join(HERE, template), encoding='utf-8').read()
    html = (html.replace('/*DATA*/', json.dumps(data))
                .replace('/*LOGO*/', logo)
                .replace('/*ASOFDATE*/', asof))
    path = os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(html)


write('bear_template.html', {'cycles': bear}, 'btc-bear-cycles/index.html')
write('bull_template.html', {'cycles': bull}, 'btc-bull-cycles/index.html')
write('halv_template.html', {'cycles': halv}, 'btc-halving-cycles/index.html')
print(json.dumps({'last_bar': str(last_bar.date()), 'built': [
    'btc-bear-cycles/index.html', 'btc-bull-cycles/index.html', 'btc-halving-cycles/index.html']}))
