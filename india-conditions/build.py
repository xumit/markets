#!/usr/bin/env python3
"""Rebuild india-conditions.html from the saved price history.

Usage (from the repository root):

    python3 india-conditions/build.py                     # rebuild only
    python3 india-conditions/build.py --new new_bars.json # merge new bars, then rebuild

new_bars.json holds the bars just pulled from TradingView, one entry per symbol,
copied from get_ohlcv's format="columns" output:

    {"NSE:NIFTY": {"t": [1791517500, ...], "c": [22551.35, ...]}, ...}

Bars are keyed by trading date, so re-sending a date replaces it (that is how a
still-forming bar gets corrected on the next run). The script refuses to save a
close that moves more than MAX_JUMP from the previous saved close, which catches
copy mistakes before they reach the public page.
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
HISTORY = HERE / "history.json"
TEMPLATE = HERE / "template.html"
OUTPUT = ROOT / "india-conditions.html"

SYMBOLS = [
    "NSE:NIFTY50EQUALWEIGHT", "NSE:NIFTY", "NSE:NIFTY500_EW", "NSE:CNX500",
    "NSE:CNXMETAL", "NSE:CNXFMCG", "NSE:CNXFINANCE", "NSE:INDIAVIX",
    "TVC:IN10Y", "TVC:VIX", "FX_IDC:USDINR", "TVC:UKOIL",
]
KEEP = 330          # trading days kept per symbol (252-day window + 20-day move + history strip + margin)
MAX_JUMP = {"NSE:INDIAVIX": 0.6, "TVC:VIX": 0.8}   # volatility indices can legitimately jump
DEFAULT_JUMP = 0.15
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def day(t):
    # TradingView stamps daily bars at the session open in UTC; +6h lands every
    # market used here (NSE 03:45Z, FX 22:00Z, Brent 22:00/00:00Z, VIX 07:15Z) on its trading date.
    return dt.datetime.fromtimestamp(int(t) + 6 * 3600, dt.timezone.utc).strftime("%Y-%m-%d")


def merge(history, new):
    problems, added = [], {}
    for sym, cols in new.items():
        if sym not in SYMBOLS:
            problems.append(f"{sym}: not one of the dashboard's symbols")
            continue
        t, c = cols.get("t") or [], cols.get("c") or []
        if len(t) != len(c) or not t:
            problems.append(f"{sym}: t has {len(t)} values but c has {len(c)}")
            continue
        rows = dict(map(tuple, history.get(sym, [])))
        incoming = sorted((day(a), float(b)) for a, b in zip(t, c) if b is not None)
        limit = MAX_JUMP.get(sym, DEFAULT_JUMP)
        for d, v in incoming:
            prev = [x for x in sorted(rows) if x < d]
            if prev:
                p = rows[prev[-1]]
                if p and abs(v / p - 1) > limit:
                    problems.append(f"{sym} {d}: close {v} is {abs(v / p - 1):.0%} away from {p} on {prev[-1]}")
                    continue
            if rows.get(d) != v:
                added.setdefault(sym, []).append(d)
            rows[d] = v
        history[sym] = [[d, rows[d]] for d in sorted(rows)][-KEEP:]
    return problems, added


def render(history):
    missing = [s for s in SYMBOLS if not history.get(s)]
    if missing:
        sys.exit("No history for: " + ", ".join(missing))
    html = TEMPLATE.read_text()
    if "/*__DATA__*/null" not in html or "/*__UPDATED__*/" not in html:
        sys.exit("template.html is missing its data placeholders")
    data = json.dumps({s: history[s] for s in SYMBOLS}, separators=(",", ":"))
    now = dt.datetime.now(IST)
    stamp = f"{now.day} {now:%b %Y, %H:%M} IST"
    html = html.replace("/*__DATA__*/null", data).replace("/*__UPDATED__*/", stamp)
    OUTPUT.write_text(html)
    return stamp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", help="JSON file of new bars to merge before rebuilding")
    args = ap.parse_args()

    history = json.loads(HISTORY.read_text()) if HISTORY.exists() else {}
    if args.new:
        problems, added = merge(history, json.loads(pathlib.Path(args.new).read_text()))
        for sym in SYMBOLS:
            if sym in added:
                print(f"updated {sym}: {', '.join(added[sym][-5:])}")
        if problems:
            print("NOT SAVED — fix these and run again:\n  " + "\n  ".join(problems))
            sys.exit(1)
        HISTORY.write_text(json.dumps(history, separators=(",", ":")))
    stamp = render(history)
    last = {s: history[s][-1][0] for s in SYMBOLS}
    print(f"built {OUTPUT.name} at {stamp}; latest dates: " +
          ", ".join(f"{s.split(':')[1]} {d}" for s, d in last.items()))


if __name__ == "__main__":
    main()
