# Important Constraints

The following notes outline current constraints and assumptions that
users should be aware of when working with LIBB.

---

## Lack of Market Data Sources

Yahoo Finance (`yfinance`) and Stooq are currently the sole active market data
sources. Finnhub and Alpha Vantage implementations exist in
`libb/execution/get_market_data.py` but are not yet wired into the main
orchestrator. Support for these sources is pending the config system described
in the roadmap.

---

## News Data Limited to Current Day

The news functions in `libb/user_data/news.py` rely on `yfinance` and only
return headlines available on the current day. There is no access to historical
news, no pagination, and no date filtering.

This means news data is not available during backtesting runs. Any prompt that
includes portfolio or macro news will receive current-day headlines regardless
of the run date, which may introduce inconsistencies in historical simulations.

---

## Manual Parsing of Model Outputs

Order extraction and structured data generation rely on manual parsing
of model-generated outputs. The framework does not enforce schema
validation or automatic correction, and users are responsible for
ensuring parsed data is well-formed before execution.

---

## Metrics Are Single-Run

Behavioral and performance metrics are computed from a single experimental
run. They describe observed behavior within that run and do not capture
variability across repeated runs or alternative initial conditions.
Cross-run comparisons require consistent experimental conditions — same
starting capital, prompts, model settings, and date range.

---

## Ongoing Development

LIBB is under active development,
so workflows and assumptions will likely become outdated when updating versions.
Always review docs and revise the system as outlined beforehand.

---

## Behavioral Metrics — Partial Implementation

Core behavioral metrics (HHI, loss aversion, turnover, cash allocation,
position counts, order quality) are implemented and available via
`libb.generate_behavior_metrics()`. Several additional metrics
(`momentum_factor`, `volatility_tolerance`, `risk_aversion`) exist as stubs
in `libb/metrics/behavior_metrics.py` and are not yet implemented.

---

## Stability

LIBB has limited automated test coverage.
Expect rough edges, especially outside the documented workflow.
Bug reports and pull requests are welcome.
