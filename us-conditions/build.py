#!/usr/bin/env python3
"""Rebuild us-conditions.html from the saved price history.

Usage (from the repository root):

    python3 us-conditions/build.py                     # rebuild only
    python3 us-conditions/build.py --new new_bars.json # merge new bars, then rebuild

new_bars.json holds the bars just pulled from TradingView, one entry per symbol,
copied from get_ohlcv's format="columns" output:

    {"AMEX:SPY": {"t": [1791517500, ...], "c": [759.97, ...]}, ...}

Bars are keyed by date, so re-sending a date replaces it (that is how a
still-forming bar gets corrected on the next run). Bars dated today or later
(India time) are ignored: when this runs in the Indian morning, those are the
next US session still forming. The script refuses to save a close that moves
more than its symbol's jump limit from the previous saved close, which catches
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
OUTPUT = ROOT / "us-conditions.html"

# symbol: (interval, trading days kept, largest believable move between saved closes; None = no check)
SPECS = {
    "AMEX:RSP": ("1D", 330, 0.15), "AMEX:SPY": ("1D", 330, 0.15),
    "AMEX:HYG": ("1D", 330, 0.15), "NASDAQ:IEF": ("1D", 330, 0.15),
    "AMEX:CPER": ("1D", 330, 0.15), "AMEX:GLD": ("1D", 330, 0.15),
    "AMEX:UUP": ("1D", 330, 0.10),
    "CBOE:VIX": ("1D", 330, 0.8), "CBOE:VIX3M": ("1D", 330, 0.6),
    "TVC:US10Y": ("1D", 330, 0.15),
    "FRED:BAMLH0A0HYM2": ("1D", 330, 0.35), "FRED:BAMLH0A3HYC": ("1D", 330, 0.35),
    "FRED:BAMLH0A1HYBB": ("1D", 330, 0.35),
    "FRED:SOFR": ("1D", 330, 0.5), "FRED:IORB": ("1D", 470, 0.3),
    "FRED:RRPONTSYD": ("1D", 1500, None),       # reverse repo can swing from near zero
    "FRED:BAA10Y": ("1W", 100000, 0.3),         # weekly, full history since 1986
}
SYMBOLS = list(SPECS)
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def day(t):
    # Same rule as the India page and the live artifact: +6h puts every bar on its trading date.
    return dt.datetime.fromtimestamp(int(t) + 6 * 3600, dt.timezone.utc).strftime("%Y-%m-%d")


def merge(history, new, today):
    problems, added = [], {}
    for sym, cols in new.items():
        if sym not in SPECS:
            problems.append(f"{sym}: not one of the dashboard's symbols")
            continue
        _, keep, limit = SPECS[sym]
        t, c = cols.get("t") or [], cols.get("c") or []
        if len(t) != len(c) or not t:
            problems.append(f"{sym}: t has {len(t)} values but c has {len(c)}")
            continue
        rows = dict(map(tuple, history.get(sym, [])))
        incoming = sorted((day(a), float(b)) for a, b in zip(t, c) if b is not None)
        for d, v in incoming:
            if d >= today:
                continue
            prev = [x for x in sorted(rows) if x < d]
            if prev and limit is not None:
                p = rows[prev[-1]]
                if p and abs(v / p - 1) > limit:
                    problems.append(f"{sym} {d}: close {v} is {abs(v / p - 1):.0%} away from {p} on {prev[-1]}")
                    continue
            if rows.get(d) != v:
                added.setdefault(sym, []).append(d)
            rows[d] = v
        history[sym] = [[d, rows[d]] for d in sorted(rows)][-keep:]
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
        today = dt.datetime.now(IST).strftime("%Y-%m-%d")
        problems, added = merge(history, json.loads(pathlib.Path(args.new).read_text()), today)
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
