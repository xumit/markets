# markets

Public dashboards for Indian equities, built from the daily NSE bhavcopy.

- `indian-market-today/index.html` — **Indian Market Today** (tools.xumitcapital.com/indian-market-today/): index levels and trailing returns across
  80 NSE indices, a debt section, factor spreads against their parent universes,
  market breadth, bullish percent indexes, and new highs and lows.
- `india-conditions.html` — **India Conditions Readout** (tools.xumitcapital.com/india-conditions.html): nine market-wide measures
  (breadth, rupee, 10-year G-sec volatility, India VIX, India vs US fear, growth,
  financials, crude in rupees), each scored as a z-score against its own past year.
  Built from TradingView daily closes kept in `india-conditions/history.json`;
  `india-conditions/build.py` merges each session's new bars and regenerates the page.

- `india-breadth/index.html` — **India Breadth Monitor** (tools.xumitcapital.com/india-breadth/):
  daily Nifty 500 advance/decline and moving-average breadth, and the distribution of
  returns and drawdowns across liquid NSE stocks. Built in `xumit/markets-data` with the
  evening update.
- `us-breadth/` — **US Breadth Monitor** (tools.xumitcapital.com/us-breadth/): daily S&P 500
  advance/decline and moving-average breadth. Rebuilt by `.github/workflows/us-breadth.yml`
  after each US session from Wikipedia's member list and Yahoo Finance closes
  (`us-breadth/build.py`).
- `us-conditions.html` — **US Conditions Readout** (tools.xumitcapital.com/us-conditions.html):
  six systemic US measures (breadth, credit, copper vs gold, dollar, VIX term structure,
  10-year Treasury yield volatility) scored against their own past year, plus credit
  spreads and funding plumbing. Built by `us-conditions/build.py` from
  `us-conditions/history.json`, the same way as the India page.
- `btc-monthly-returns/index.html` — **XC Bitcoin Monthly Returns** (tools.xumitcapital.com/btc-monthly-returns/):
  month-by-year returns of Bitcoin (USD, month-end close to month-end close) for all data, the last
  10 years and the last 5 years, with statistics by calendar month and by election-cycle group.
  Self-contained: the monthly returns are embedded in the page. Updated each day from TradingView
  (INDEX:BTCUSD) by the steps in `btc-monthly-returns/build/`: `history.json` holds the daily closes,
  `update_history.py` merges the newest closed bars, and `build_page.py` rebuilds the page from
  `template.html`.
- `btc-bear-cycles/index.html` — **Bitcoin Bear Cycles** (tools.xumitcapital.com/btc-bear-cycles/):
  the five bear cycles from their peaks, rebased to 1.00, with an average line. Click a cycle name to
  show or hide its line. Includes a summary table. Self-contained; figures from TradingView daily closes.
- `btc-bull-cycles/index.html` — **Bitcoin Bull Cycles** (tools.xumitcapital.com/btc-bull-cycles/):
  the six bull cycles from their starting closes, rebased to 1.00, on a log scale. Median or mean
  average, with Bull Cycle 1 optional. Click a cycle name to show or hide its line. Self-contained;
  figures from TradingView daily closes.
- `btc-halving-cycles/index.html` — **Bitcoin Halving-to-Halving Cycles** (tools.xumitcapital.com/btc-halving-cycles/):
  each period between halvings from its starting close, rebased to 1.00, on a log scale. Median or mean
  average, with H-H Cycle 1 optional. Click a cycle name to show or hide its line. Self-contained; figures from TradingView daily closes.
- `sp500-monthly-returns/index.html` — **XC S&P 500 Monthly Returns** (tools.xumitcapital.com/sp500-monthly-returns/):
  monthly price-index returns of the S&P 500 (dividends not included), for all data from 1927 and since 1942,
  with statistics by calendar month and by election-cycle group. Self-contained.
- `index.html` — a fixed redirect to `indian-market-today/`. Do not overwrite it.

The page is self-contained: all data for the as-of date is embedded, so there is
nothing to fetch and no backend. It is regenerated after each trading session
from that day's price report and pushed here; GitHub Pages serves it.

Prices are adjusted for splits, bonuses and demergers using NSE's own corporate
action records. Trailing windows are calendar-anchored, so holidays never shift
them. Nothing here is investment advice.
