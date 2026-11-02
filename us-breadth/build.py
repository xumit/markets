#!/usr/bin/env python3
"""Build the US Breadth Monitor (tools.xumitcapital.com/us-breadth/).

Runs on GitHub Actions after each US session (.github/workflows/us-breadth.yml):

  1. reads today's S&P 500 member list from Wikipedia
  2. downloads two years of daily closes for every member, and the S&P 500
     index itself, from Yahoo Finance (split- and dividend-adjusted)
  3. for every session counts members that closed up and down, and the share
     closing above their own 20 / 50 / 200-day simple moving average
  4. writes us-breadth/data.json and us-breadth/index.html

Nothing is written unless the checks at the end of main() pass, so a bad
download leaves yesterday's page in place rather than publishing nonsense.

Usage:  python3 us-breadth/build.py            (needs network: Wikipedia, Yahoo)
        python3 us-breadth/build.py --render   (rebuild the page from data.json)
"""
import argparse
import datetime as dt
import io
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "template.html"
DATA = HERE / "data.json"
OUT = HERE / "index.html"

MAS = [20, 50, 200]
KEEP = 260                      # sessions published, about a year
MIN_MEMBERS = 490               # refuse to publish if fewer members have prices
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
WIKI = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def members():
    import pandas as pd
    import requests
    html = requests.get(WIKI, headers={"User-Agent": "Mozilla/5.0 (xumitcapital breadth)"}, timeout=60).text
    t = pd.read_html(io.StringIO(html), attrs={"id": "constituents"})[0]
    syms = sorted({str(s).strip().replace(".", "-") for s in t["Symbol"]})
    if not 495 <= len(syms) <= 510:
        sys.exit(f"member list has {len(syms)} symbols — Wikipedia's table may have changed")
    return syms


def compute():
    import numpy as np
    import pandas as pd
    import yfinance as yf

    syms = members()
    px = yf.download(syms, period="2y", interval="1d", auto_adjust=True,
                     progress=False, threads=True, group_by="column")["Close"]
    ix = yf.download("^GSPC", period="2y", interval="1d", auto_adjust=True,
                     progress=False)["Close"]
    if isinstance(ix, pd.DataFrame):
        ix = ix.iloc[:, 0]
    px.index = pd.to_datetime(px.index).tz_localize(None).normalize()
    ix.index = pd.to_datetime(ix.index).tz_localize(None).normalize()
    ix = ix.dropna()

    # Only sessions the index itself traded; a row of all-NaN prices is not a session.
    px = px.reindex(ix.index)
    priced = [s for s in px.columns if px[s].notna().sum() > 0]
    missing = sorted(set(syms) - set(priced))
    c = px[priced]

    chg = c.pct_change(fill_method=None)
    live = c.notna() & c.shift(1).notna()
    adv = ((chg > 0) & live).sum(axis=1)
    dec = ((chg < 0) & live).sum(axis=1)
    unch = ((chg == 0) & live).sum(axis=1)
    ma = {}
    for n in MAS:
        avg = c.rolling(n, min_periods=n).mean()
        ok = avg.notna() & c.notna()
        ma[n] = ((c > avg) & ok).sum(axis=1) / ok.sum(axis=1).replace(0, np.nan) * 100

    rows = []
    for d in c.index[-KEEP:]:
        r = [d.strftime("%Y-%m-%d"), int(adv[d]), int(dec[d]), int(unch[d])]
        r += [None if not np.isfinite(ma[n][d]) else round(float(ma[n][d]), 1) for n in MAS]
        r.append(round(float(ix[d]), 2))
        rows.append(r)

    # Checks. The last session must have prices for nearly every member (a
    # half-finished download shows up as a collapse in adv + dec).
    last = rows[-1]
    counted = last[1] + last[2] + last[3]
    problems = []
    if len(priced) < MIN_MEMBERS:
        problems.append(f"only {len(priced)} members have prices")
    if counted < MIN_MEMBERS:
        problems.append(f"only {counted} members priced on {last[0]}")
    if any(v is None for v in last[4:7]):
        problems.append(f"moving-average shares missing on {last[0]}")
    if problems:
        sys.exit("NOT PUBLISHED: " + "; ".join(problems))
    return {"universe": "S&P 500", "members": len(priced), "missing": missing,
            "cols": ["date", "adv", "dec", "unch"] + [f"ma{n}" for n in MAS] + ["close"],
            "rows": rows}


def render(daily):
    now = dt.datetime.now(IST)
    blob = {"daily": daily, "updated": f"{now.day} {now:%b %Y, %H:%M} IST"}
    html = TEMPLATE.read_text()
    if "/*__DATA__*/null" not in html:
        sys.exit("template.html is missing its data placeholder")
    OUT.write_text(html.replace("/*__DATA__*/null", json.dumps(blob, separators=(",", ":"))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true", help="rebuild the page from data.json only")
    a = ap.parse_args()
    if a.render:
        daily = json.loads(DATA.read_text())
    else:
        daily = compute()
        old = json.loads(DATA.read_text()) if DATA.exists() else None
        if old and daily["rows"][-1][0] < old["rows"][-1][0]:
            sys.exit(f"NOT PUBLISHED: download ends {daily['rows'][-1][0]}, "
                     f"older than the page's {old['rows'][-1][0]}")
        DATA.write_text(json.dumps(daily, separators=(",", ":")))
    render(daily)
    last = daily["rows"][-1]
    print(f"{daily['universe']}: {daily['members']} members"
          + (f" (no prices: {', '.join(daily['missing'])})" if daily.get("missing") else ""))
    print(f"latest {last[0]}: up {last[1]} down {last[2]} flat {last[3]} · "
          f">20d {last[4]}% >50d {last[5]}% >200d {last[6]}% · index {last[7]}")


if __name__ == "__main__":
    main()
