# Roadmap (Short Term)

This roadmap outlines near-term development priorities for LIBB.
Items are ordered by importance and reflect concrete, actionable goals rather
than long-term vision.

This document is intentionally limited in scope and subject to change.

---

## Top Priorities

### 1. Behavioral Metrics

Complete the behavioral metrics framework to quantify patterns in model
decision-making.

Planned focus areas:

- bias-related signals
- consistency and repetition analysis
- response patterns across similar conditions
- add wrapper in main class

Behavioral metrics are intended for research and analysis, not enforcement.

---

## 2. Config File Creation

Introduce a structured JSON configuration system to centralize experiment
parameters and backend behavior controls.

Goals:

- create a default configuration schema covering:
  - market assumptions (risk-free rate, baseline ticker, trading days)
  - portfolio parameters (initial capital, fractional shares, cash buffer)
  - LLM execution settings (temperature, seed, determinism)
  - data source preferences
  - metric toggles
- auto-generate a default config file if none exists
- allow partial overrides without requiring full specification
- enforce schema validation to prevent silent misconfiguration
- ensure all experiments are reproducible via serialized config snapshot

The configuration system will serve as the backbone for experimental control
while preserving flexibility for research use cases.

---

### 3. Multiple Data Source Support

Add support for multiple market data sources besides Stooq and `yfinance`.

Goals:

- add functions supporting other APIs
- ensure returned data matches existing format (MarketHistoryObject/MarketDataObject)
- rewire functions into the main orchestrator

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
