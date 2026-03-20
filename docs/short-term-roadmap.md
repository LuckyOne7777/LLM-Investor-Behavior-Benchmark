# Roadmap (Short Term)

This roadmap outlines near-term development priorities for LIBB.
Items are ordered by importance and reflect concrete, actionable goals rather
than long-term vision.

This document is intentionally limited in scope and subject to change.

---

## Top Priorities

### 1. Multiple Data Source Support

Wire existing market data source implementations into the main orchestrator.

Finnhub and Alpha Vantage functions already exist in
`libb/execution/get_market_data.py` but are not currently used.
`download_data_on_given_range()` still hardcodes `["yf", "stooq"]` rather
than calling `get_valid_data_sources()`.

Goals:

- complete the config system (priority 2) first to handle API key management
  and source preference ordering
- wire `get_valid_data_sources()` into `download_data_on_given_range()`
- validate that Finnhub and Alpha Vantage return data matching the existing
  `MarketHistoryObject` / `MarketDataObject` format

---

### 2. Fractional Share Support

Add first-class support for fractional share trading across order handling,
portfolio state, and accounting logic.

Goals:

- allow non-integer share quantities in orders
- update position tracking to support fractional holdings
- ensure cash debits and credits reflect precise fractional execution
- maintain numerical stability and rounding consistency

This change requires careful treatment of floating-point precision and may
affect validation logic, logging, and performance calculations.

---

## Notes

- Ordering reflects current priorities and may change
- This roadmap does not imply timelines or guarantees
- Long-term vision is still being decided
