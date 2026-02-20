# Metrics

Metrics provide derived, quantitative signals from model outputs and portfolio
state. They are optional, advisory, and do not directly influence order
generation unless explicitly used by the user.

All metric functions are intended to be called **after**
`process_portfolio()` has been executed.

---

## Sentiment

Sentiment metrics analyze model-generated text and extract interpretable
sentiment signals. These metrics are informational only and are primarily
intended for logging, analysis, and research workflows.

Sentiment analysis does not modify portfolio state or trading decisions.

---

### analyze_sentiment

```libb.analyze_sentiment(text: str, report_type: str = "Unknown") -> dict```

Analyzes sentiment for the provided text and persists the result.

The sentiment log is:

- appended to the in-memory sentiment list
- written to disk as JSON
- returned to the caller

---

### Parameters

- `text` (`str`)  
  Text to analyze (typically raw model output).

- `report_type` (`str`, optional)  
  Identifier describing the source or type of the report.  
  Defaults to `"Unknown"`.

---

### Requirements

- `process_portfolio()` must have been called
- Input text should be complete model output (daily or weekly reports)

---

### State Interaction

Reads:

- `self.date`

Writes:

- `self.sentiment`
- `self.sentiment_path`

---

### Example Usage

```python
from libb import LIBBmodel

libb = LIBBmodel("user_side/runs/run_v1/model_a")

daily_report = prompt_daily_report(libb)
sentiment_log = libb.analyze_sentiment(
daily_report,
report_type="Daily"
)
print(sentiment_log)
```

---

### Example Output

```python
[
{
"subjectivity": 0.17369308571046696,
"polarity": -0.3980582485625413,
"positive_count": 31,
"negative_count": 72,
"token_count": 593,
"report_type": "Daily",
"date": "2025-12-28"
}
]
```

---

### Notes

- Sentiment metrics are advisory and informational only
- Results are not consumed internally by LIBB
- Users may ignore, extend, or replace this metric

## Performance

Performance metrics provide quantitative evaluation of portfolio behavior
relative to time, volatility, and a chosen market benchmark.

These metrics are analytical only. They do not modify portfolio state,
execution flow, or trading decisions.

All performance calculations are intended to be run **after**
`process_portfolio()` has been executed and at least one portfolio
history entry exists.

---

## generate_performance_metrics

```python
libb.generate_performance_metrics(baseline_ticker: str = "^SPX") -> None
```

Generates comprehensive performance metrics for the portfolio and
persists the results to disk.

This method:

- Loads portfolio equity history
- Downloads benchmark data via `yfinance`
- Computes risk and return statistics
- Computes CAPM metrics
- Saves the compiled metrics log to `metrics/performance.json`

---

### Parameters

- `baseline_ticker` (`str`, optional)  
  Market benchmark used for relative performance comparison.  
  Defaults to `"^SPX"`.

---

### Requirements

- `process_portfolio()` must have been called at least once
- `portfolio_history.csv` must not be empty
- Portfolio history must not contain duplicate dates
- Internet access is required for benchmark download

---

### State Interaction

Reads:

- `self.layout.portfolio_history_path`
- `self.run_date`

Writes:

- Performance metrics file via `self.writer.save_performance()`

---

### Defined Observation Range

observation_count: The number of valid daily return periods calculated.

observation_start: The date of the first price movement (Inception). Note that while the slice starts here to establish a cost basis,
the first return observation occurs on the following period.

### Metrics Computed

- `volatility_daily`  
  Standard deviation of daily returns.

- `sharpe_ratio_daily`  
  Daily Sharpe ratio (risk-free adjusted).

- `sharpe_ratio_annualized`  
  Annualized Sharpe ratio (√252 scaling).

- `sortino_ratio_daily`  
  Downside-risk-adjusted daily return metric.

- `sortino_ratio_annualized`  
  Annualized Sortino ratio.

---

### Drawdown

- `max_drawdown_pct`  
  Maximum observed equity decline from peak.

- `max_drawdown_date`  
  Date at which maximum drawdown occurred.

---

### CAPM Metrics

- `capm_beta`  
  Sensitivity to market returns.

- `capm_alpha_annualized`  
  Annualized excess return beyond CAPM expectation.

- `capm_r_squared`  
  Goodness-of-fit to the market factor.

---

### Metadata

- `start_date`  
  First active equity date.

- `end_date`  
  Last portfolio history date.

- `observation_count`  
  Number of daily return observations used.

- `generated_at`  
  Run date for the metrics generation.

---

## Example Usage

```python
from libb import LIBBmodel

libb = LIBBmodel("user_side/runs/run_v1/model_a")

libb.process_portfolio()
performance_log = libb.generate_performance_metrics(baseline_ticker="^SPX")
print(performance_log)
```

---

## Example Output

```python
{
  "volatility_daily": 0.0123,
  "sharpe_ratio_daily": 0.084,
  "sharpe_ratio_annualized": 1.33,
  "sortino_ratio_daily": 0.091,
  "sortino_ratio_annualized": 1.45,
  "max_drawdown_pct": -0.182,
  "max_drawdown_date": "2026-01-17",
  "capm_beta": 1.12,
  "capm_alpha_annualized": 0.041,
  "capm_r_squared": 0.76,
  "start_date": "2025-11-01",
  "end_date": "2026-02-15",
  "observation_count": 63,
  "generated_at": "2026-02-15"
}
```

---

## Notes

- Benchmark data is currently downloaded using `yfinance`
- Yeearly risk-free rate defaults to 4.5% annualized unless modified internally
- Metrics are computed using daily returns
- Annualization assumes 252 trading days
- Results are advisory and informational only
- LIBB does not internally consume these metrics

---
