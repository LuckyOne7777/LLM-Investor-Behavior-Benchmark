# Roadmap (Short Term)

This roadmap outlines near-term development priorities for LIBB.
Items are ordered by importance and reflect concrete, actionable goals rather
than long-term vision.

This document is intentionally limited in scope and subject to change.

---

## Top Priorities

### 1. Behavioral Metrics

The core behavioral metrics framework is implemented and available via
`libb.generate_behavior_metrics()`. The following metrics are complete:

- HHI-based concentration (with cash as explicit position)
- Loss aversion ratio
- Turnover ratio
- Cash allocation (average and median)
- Position counts (average, median, max per day)
- Order quality counts (filled, failed, rejected by side)

The following metrics exist as stubs and are not yet implemented:

- `momentum_factor` — correlation between past k-day return and buy decisions
- `volatility_tolerance` — willingness to hold volatile positions
- `risk_aversion` — frequency of risk reduction following losses

Remaining work:

- implement the stub metrics above
- add wrapper in main class for any new metrics
- add behavioral metrics to the docs metrics capability page

Behavioral metrics are intended for research and analysis, not enforcement.

---

### 2. Config File Creation

Introduce a structured JSON configuration system to centralize experiment
parameters and backend behavior controls.

This is a prerequisite for the data source wiring in priority 3, as the
config will manage API key preferences and source priority ordering.

Goals:

- create a default configuration schema covering:
  - market assumptions (risk-free rate, baseline ticker, trading days)
  - portfolio parameters (initial capital, fractional shares, cash buffer)
  - LLM execution settings (temperature, seed, determinism)
  - data source preferences and priority ordering
  - metric toggles
- auto-generate a default config file if none exists
- allow partial overrides without requiring full specification
- enforce schema validation to prevent silent misconfiguration
- ensure all experiments are reproducible via serialized config snapshot

The configuration system will serve as the backbone for experimental control
while preserving flexibility for research use cases.

---

### 3. Multiple Data Source Support

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

### 4. Fractional Share Support

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
