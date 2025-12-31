# Important Constraints

The following notes outline current constraints and assumptions that
users should be aware of when working with LIBB.

---

## Minimum Portfolio Requirements

At least one ticker must remain in the portfolio at all times to
maintain correct cash accounting. Fully liquidating all positions may
lead to inconsistent or undefined behavior in downstream calculations.

---

## Trading Calendar Assumptions

LIBB assumes execution on U.S. trading days only. The framework does not
currently account for weekends or market holidays, and workflows should
avoid running on non-trading days.

---

## Market Data Source

Yahoo Finance (`yfinance`) is currently the sole supported market data
source. Data availability, accuracy, and rate limits are therefore
subject to Yahoo Finance constraints.

---

## Manual Parsing of Model Outputs

Order extraction and structured data generation rely on manual parsing
of model-generated outputs. The framework does not enforce schema
validation or automatic correction, and users are responsible for
ensuring parsed data is well-formed before execution.

---

## Ongoing Development and Stability

LIBB is an actively evolving research system. Version 1 prioritizes explicit state,
reproducibility, and conceptual clarity over feature completeness or long-term API
stability.

Many of the constraints listed in this document reflect the current design and are
not guaranteed to persist across future versions. Interfaces, workflows, and internal
assumptions may change as the system matures and new research requirements emerge.

---

## Lack of Supported Metrics

For Version 1, the focus was just getting the system reliable and consistent, so right now the only supported metric class is sentiment. However, functions for performance functions have been created and just need to be connected.

---

## Stability 

LIBB has limited automated test coverage.
Expect rough edges, especially outside the documented course.
Bug reports and pull requests are welcome.
    


