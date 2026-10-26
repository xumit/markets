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
- `us-conditions.html` — **US Conditions Readout** (tools.xumitcapital.com/us-conditions.html):
  six systemic US measures (breadth, credit, copper vs gold, dollar, VIX term structure,
  10-year Treasury yield volatility) scored against their own past year, plus credit
  spreads and funding plumbing. Built by `us-conditions/build.py` from
  `us-conditions/history.json`, the same way as the India page.
- `index.html` — a fixed redirect to `indian-market-today/`. Do not overwrite it.

The page is self-contained: all data for the as-of date is embedded, so there is
nothing to fetch and no backend. It is regenerated after each trading session
from that day's price report and pushed here; GitHub Pages serves it.

Prices are adjusted for splits, bonuses and demergers using NSE's own corporate
action records. Trailing windows are calendar-anchored, so holidays never shift
them. Nothing here is investment advice.
