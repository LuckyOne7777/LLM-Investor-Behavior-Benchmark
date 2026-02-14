# Important Constraints

The following notes outline current constraints and assumptions that
users should be aware of when working with LIBB.

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

## Ongoing Development

LIBB is under active development,
so workflows and assumptions will likely become outdated when updating versions.
Always review docs and revise the system as outlined beforehand.

---

## Lack of Supported Metrics

Right now the only supported metric class is sentiment.
More metric classes are planned and outlined in the roadmap.

---

## Stability

LIBB has limited automated test coverage.
Expect rough edges, especially outside the documented course.
Bug reports and pull requests are welcome.
