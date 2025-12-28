# Important Notes

The following notes outline current constraints and assumptions that
users should be aware of when working with LIBB.

*Please note that these are constraints of the current design and may be addressed by feature updates.*

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
