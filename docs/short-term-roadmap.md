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

Behavioral metrics are intended for research and analysis, not enforcement.

---

### 2. Multiple Data Source Support

Add support for multiple market data sources.

Goals:

- configurable primary data source
- ability to switch sources without code changes
- consistent data interface across sources

---

### 3. Data Source Fallbacks

Provide automatic or user-defined fallback mechanisms when a primary data source
fails or returns incomplete data.

Goals:

- improve robustness of runs
- reduce silent failures
- preserve reproducibility across environments

Fallback behavior should be explicit and auditable.

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
