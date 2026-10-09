# markets

Public dashboards for Indian equities, built from the daily NSE bhavcopy.

- `index.html` — **Indian Market Today**: index levels and trailing returns across
  80 NSE indices, a debt section, factor spreads against their parent universes,
  market breadth, bullish percent indexes, and new highs and lows.
- `india-conditions.html` — **India Conditions Readout**: nine market-wide measures
  (breadth, rupee, 10-year G-sec volatility, India VIX, India vs US fear, growth,
  financials, crude in rupees), each scored as a z-score against its own past year.
  Built from TradingView daily closes kept in `india-conditions/history.json`;
  `india-conditions/build.py` merges each session's new bars and regenerates the page.

The page is self-contained: all data for the as-of date is embedded, so there is
nothing to fetch and no backend. It is regenerated after each trading session
from that day's price report and pushed here; GitHub Pages serves it.

Prices are adjusted for splits, bonuses and demergers using NSE's own corporate
action records. Trailing windows are calendar-anchored, so holidays never shift
them. Nothing here is investment advice.
