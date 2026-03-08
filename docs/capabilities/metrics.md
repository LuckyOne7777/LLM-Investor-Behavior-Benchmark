# Metrics

Metrics provide derived, quantitative signals from model outputs and portfolio
state. They are optional, advisory, and do not directly influence order
generation unless explicitly used by the user.

All metric functions are intended to be called **after**
`process_portfolio()` has been executed.

---

## Sentiment

Sentiment metrics analyze model-generated text and extract interpretable
sentiment signals using the Loughran-McDonald financial lexicon, which is
purpose-built for financial text and differs from general-purpose sentiment
tools by treating words like "liability" and "risk" as negative rather than
neutral.

Sentiment analysis does not modify portfolio state or trading decisions.

---

### analyze_sentiment

```python
libb.analyze_sentiment(text: str, report_type: str = "Unknown") -> dict
```

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

- `self.run_date`

Writes:

- `self.sentiment`
- `self.layout.sentiment_path`

---

### Example Usage

```python
from libb import LIBBmodel

libb = LIBBmodel("user_side/runs/run_v1/model_a")

libb.process_portfolio()
daily_report = prompt_daily_report(libb)
sentiment_log = libb.analyze_sentiment(daily_report, report_type="Daily")
print(sentiment_log)
```

---

### Example Output

```python
{
    "subjectivity": 0.17369308571046696,
    "polarity": -0.3980582485625413,
    "positive_count": 31,
    "negative_count": 72,
    "token_count": 593,
    "report_type": "Daily",
    "date": "2025-12-28"
}
```

---

### Metrics Computed

- `subjectivity`
  Ratio of opinion-bearing tokens to total tokens. Range 0.0 to 1.0.

- `polarity`
  Net sentiment score, positive minus negative normalized by total tokens.
  Range -1.0 to 1.0.

- `positive_count`
  Number of positive tokens identified by the Loughran-McDonald lexicon.

- `negative_count`
  Number of negative tokens identified by the Loughran-McDonald lexicon.

- `token_count`
  Total number of tokens in the analyzed text.

---

### Notes

- Sentiment metrics are advisory and informational only
- Results are not consumed internally by LIBB
- Users may ignore, extend, or replace this metric
- The Loughran-McDonald lexicon is optimized for financial text and may
  produce different results than general-purpose sentiment tools on the
  same input

---

## Performance

Performance metrics provide quantitative evaluation of portfolio behavior
relative to time, volatility, and a chosen market benchmark.

These metrics are analytical only. They do not modify portfolio state,
execution flow, or trading decisions.

All performance calculations are intended to be run **after**
`process_portfolio()` has been executed and at least one portfolio
history entry exists.

---

### generate_performance_metrics

```python
libb.generate_performance_metrics(baseline_ticker: str = "^SPX") -> dict
```

Generates comprehensive performance metrics for the portfolio and
persists the results to disk.

This method:

- Loads portfolio equity history and trade execution log
- Downloads benchmark data via `yfinance`
- Computes risk and return statistics
- Computes CAPM metrics
- Computes trade-level statistics from filled sell orders
- Appends the compiled metrics log to `metrics/performance.json`

---

### Parameters

- `baseline_ticker` (`str`, optional)
  Market benchmark used for CAPM and relative performance calculations.
  Defaults to `"^SPX"`. Must be accessible via yfinance.

---

### Requirements

- `process_portfolio()` must have been called at least once
- `portfolio_history.csv` must not be empty
- Portfolio equity must have changed from its initial value at least once
- Internet access is required for benchmark download

---

### State Interaction

Reads:

- `self.layout.portfolio_history_path`
- `self.layout.trade_log_path`
- `self.run_date`

Writes:

- `self.performance`
- `self.layout.performance_path`

---

### Defined Observation Range

The observation period begins at the first date where portfolio equity
changed from its initial value, excluding the flat pre-trade period.
This ensures metrics are computed over the period where the model was
actively trading rather than from inception.

`observation_count` is the number of valid daily return periods within
this window.

---

### Metrics Computed

#### Equity Curve

- `volatility_daily`
  Standard deviation of daily returns (ddof=1).

- `sharpe_ratio_daily`
  Daily Sharpe ratio, risk-free adjusted at 4.5% annualized.

- `sharpe_ratio_annualized`
  Annualized Sharpe ratio scaled by √252.

- `sortino_ratio_daily`
  Daily Sortino ratio using downside deviation only.

- `sortino_ratio_annualized`
  Annualized Sortino ratio scaled by √252.

---

#### Drawdown

- `max_drawdown_pct`
  Maximum observed peak-to-trough equity decline as a negative percentage.

- `max_drawdown_date`
  Date at which maximum drawdown occurred.

---

#### CAPM

- `capm_beta`
  Sensitivity of portfolio returns to benchmark returns.

- `capm_alpha_annualized`
  Annualized excess return beyond CAPM expectation.

- `capm_r_squared`
  Goodness-of-fit to the market factor. Low values indicate the
  benchmark is not a reliable explanatory variable for portfolio returns.

---

#### Trade Level

Computed from filled sell orders only. All fields return `null` if no
filled sells exist.

- `trade_count`
  Total number of filled sell orders.

- `win_rate`
  Fraction of filled sells with positive PnL.

- `avg_gain`
  Mean PnL across winning trades.

- `avg_loss`
  Mean PnL across losing trades. Reported as a negative number.

- `median_gain`
  Median PnL across winning trades.

- `median_loss`
  Median PnL across losing trades. Reported as a negative number.

- `profit_factor`
  Sum of gains divided by absolute sum of losses. Values above 1.0
  indicate total gains exceed total losses.

- `expectancy`
  Expected PnL per trade in USD:

  expectancy = (avg_gain × win_rate) + (avg_loss × (1 - win_rate))

---

#### Metadata

- `start_date`
  First active equity date (inception of trading activity).

- `end_date`
  Last portfolio history date.

- `observation_count`
  Number of daily return observations used in calculations.

- `generated_at`
  Run date at time of generation.

---

### Example Usage
```python
from libb import LIBBmodel

libb = LIBBmodel("user_side/runs/run_v1/model_a")

libb.process_portfolio()
performance_log = libb.generate_performance_metrics(baseline_ticker="^SPX")
print(performance_log)
```

---

### Example Output
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
    "trade_count": 31,
    "win_rate": 0.52,
    "avg_gain": 4.21,
    "avg_loss": -3.84,
    "median_gain": 1.62,
    "median_loss": -1.47,
    "profit_factor": 1.14,
    "expectancy": 0.34,
    "start_date": "2025-11-01",
    "end_date": "2026-02-15",
    "observation_count": 63,
    "generated_at": "2026-02-15"
}
```

---

### Notes

- Benchmark data is downloaded using `yfinance`
- Annual risk-free rate defaults to 4.5% and is not currently configurable
- Metrics are computed using daily returns
- Annualization assumes 252 trading days
- Alpha and beta may be unstable with short observation windows or low R²
- Trade-level metrics are sensitive to outlier trades — inspect the raw
  trade log alongside aggregate metrics when interpreting results
- Results are advisory and informational only
- LIBB does not internally consume these metrics

---

## Behavioral

Behavioral metrics characterize LLM decision-making patterns derived from
trade execution logs, position history, and portfolio equity history.

These metrics are descriptive and observational. They do not establish
causal claims or statistical significance, and are not consumed internally
by LIBB. Interpretation and downstream analysis is left to the researcher.

Classical behavioral finance metrics were designed for human traders with
large transaction samples and emotional stakes. Direct application to LLM
agents is limited by sample size and the absence of emotional context. The
metrics in this module are adapted or purpose-built for the LLM trading
setting.

---

### generate_behavior_metrics

```python
libb.generate_behavior_metrics() -> dict
```

Computes behavioral metrics for the current run and persists the result.

This method:

- Loads trade execution logs, position history, and portfolio equity history
- Computes concentration, loss aversion, turnover, cash allocation,
  position counts, and order quality metrics
- Appends the compiled metrics log to `metrics/behavior.json`

---

### Requirements

- `process_portfolio()` must have been called at least once
- `trade_log.csv`, `position_history.csv`, and `portfolio_history.csv`
  must not be empty

---

### State Interaction

Reads:

- `self.layout.trade_log_path`
- `self.layout.position_history_path`
- `self.layout.portfolio_history_path`
- `self.run_date`

Writes:

- `self.behavior`
- `self.layout.behavior_path`

---

### Metrics Computed

#### Concentration

- `hhi_index`
  Average daily Herfindahl-Hirschman Index (HHI) across all observation
  days. Cash is treated as an explicit position, so a fully cash portfolio
  has HHI = 1.0 (maximum concentration) and an equally weighted two-stock
  portfolio has HHI = 0.5. Range 0.0 to 1.0.

#### Loss Aversion

- `loss_aversion_score`
  Ratio of average loss magnitude to average gain magnitude across all
  filled sell orders with nonzero PnL:

  ```
  λ = |avg(PnL < 0)| / avg(PnL > 0)
  ```

  Values greater than 1.0 indicate losses are larger in magnitude than
  gains on average. Directly analogous to the loss aversion coefficient
  in Kahneman and Tversky's prospect theory. Returns `null` if no gains
  or losses exist.

#### Turnover

- `turnover_ratio`
  Total value of filled trades divided by average portfolio equity.
  Measures how actively the model repositions relative to portfolio size.
  High turnover indicates frequent repositioning; low turnover indicates
  a buy-and-hold tendency.

#### Cash Allocation

- `avg_cash_pct`
  Mean daily cash balance as a percentage of total equity across all
  observation days.

- `med_cash_pct`
  Median daily cash balance as a percentage of total equity. A higher
  median than average suggests the model routinely holds excess cash
  rather than deploying capital.

#### Position Counts

- `avg_positions_per_day`
  Mean number of tickers held per trading day.

- `median_positions_per_day`
  Median number of tickers held per trading day.

- `max_positions_in_a_day`
  Maximum number of concurrent positions observed on any single day.

#### Order Quality

- `total_buy_count`
  Total buy-side orders across all statuses.

- `total_sell_count`
  Total sell-side orders across all statuses.

- `total_failed_buys`
  Buy orders with status FAILED. High values relative to total buy count
  may indicate overly aggressive limit pricing or poor liquidity awareness.

- `total_failed_sells`
  Sell orders with status FAILED.

- `total_rejected_buys`
  Buy orders with status REJECTED. Rejections indicate orders placed for
  invalid dates or closed market sessions, reflecting prompt compliance
  issues.

- `total_rejected_sells`
  Sell orders with status REJECTED.

---

### Metadata

- `start_date`
  First date in portfolio history.

- `end_date`
  Last date in portfolio history.

- `observation_count`
  Total number of trading days in portfolio history.

- `generated_at`
  Run date at time of generation.

---

### Example Usage

```python
from libb import LIBBmodel

libb = LIBBmodel("user_side/runs/run_v1/model_a")

libb.process_portfolio()
behavior_log = libb.generate_behavior_metrics()
print(behavior_log)
```

---

### Example Output

```python
{
    "loss_aversion_score": 3.006,
    "hhi_index": 0.751,
    "turnover_ratio": 4.291,
    "avg_cash_pct": 84.37,
    "med_cash_pct": 91.38,
    "avg_positions_per_day": 1.674,
    "median_positions_per_day": 1.0,
    "max_positions_in_a_day": 3,
    "total_buy_count": 34,
    "total_sell_count": 31,
    "total_failed_buys": 14,
    "total_failed_sells": 3,
    "total_rejected_buys": 6,
    "total_rejected_sells": 5,
    "start_date": "2025-01-02",
    "end_date": "2025-06-04",
    "observation_count": 103,
    "generated_at": "2025-06-05"
}
```

---

### Notes

- All metrics are computed from a single experimental run. Cross-run
  comparisons require consistent experimental conditions
- Loss aversion and turnover are sensitive to outlier trades. Inspect
  raw trade logs alongside aggregate metrics when interpreting results
- HHI averaging includes all observation days equally, including days
  with no position changes
- The failed and rejected order counts include all order types (BUY, SELL,
  UPDATE). Filter by action field in the trade log for breakdown by type
- Results are advisory and informational only
- LIBB does not internally consume these metrics