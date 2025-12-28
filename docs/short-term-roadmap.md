# Roadmap (Short Term)

This roadmap outlines near-term development priorities for LIBB.
Items are ordered by importance and reflect concrete, actionable goals rather
than long-term vision.

This document is intentionally limited in scope and subject to change.

---

## Top Priorities

### 1. Separate Cash from Portfolio State

Refactor internal state representation to ensure cash is tracked independently
from portfolio positions.

Goals:
- eliminate implicit cash coupling
- improve clarity of portfolio valuation
- reduce risk of accounting and reconciliation errors

This change is foundational and may affect downstream metrics and workflows.

---

### 2. Performance Metrics

Incorporate portfolio performance metrics to enable quantitative evaluation of
model behavior over time.

Planned focus areas:
- returns and drawdowns
- risk-adjusted performance measures
- time-series tracking of portfolio value

Performance metrics are advisory and do not influence trading decisions unless
explicitly used by the user.

---

### 3. Behavioral Metrics

Complete the behavioral metrics framework to quantify patterns in model
decision-making.

Planned focus areas:
- bias-related signals
- consistency and repetition analysis
- response patterns across similar conditions

Behavioral metrics are intended for research and analysis, not enforcement.

---

### 4. Structured Logging

Introduce a consistent, structured logging system across LIBB.

Goals:
- unified logging format for runs
- explicit logging of major lifecycle events
- improved debuggability and auditability
- separation between logs and metrics

Logging is intended for transparency and debugging, not performance analysis.

---

### 5. Multiple Data Source Support

Add support for multiple market data sources.

Goals:
- configurable primary data source
- ability to switch sources without code changes
- consistent data interface across sources

---

### 6. Data Source Fallbacks

Provide automatic or user-defined fallback mechanisms when a primary data source
fails or returns incomplete data.

Goals:
- improve robustness of runs
- reduce silent failures
- preserve reproducibility across environments

Fallback behavior should be explicit and auditable.

---

## Notes

- Ordering reflects current priorities and may change
- This roadmap does not imply timelines or guarantees
- Long-term vision is still being decided
