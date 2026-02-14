# Graphing

LIBB provides built-in visualization utilities for portfolio performance and sentiment analysis.

All graphing functions render interactive matplotlib figures and do not return values.

---

# High-Level Wrapper Methods (LIBBmodel)

These methods are available directly on a `LIBBmodel` instance and automatically use the model's internal file layout.

---

## plot_equity_and_sentiment

```python
libb.plot_equity_and_sentiment() -> None
```

Generate a two-panel figure:

- Top subplot: portfolio equity over time
- Bottom subplot: sentiment polarity over time
- Shared x-axis (date)

Internally calls:

```python
plot_equity_and_sentiment(
    self.layout.portfolio_history_path,
    self.layout.sentiment_path
)
```

---

## plot_equity_vs_baseline

```python
libb.plot_equity_vs_baseline(baseline: str = "^SPX") -> None
```

Generate a comparison graph between:

- Portfolio equity
- A baseline ticker (default: `^SPX`)

The baseline is downloaded dynamically using `yfinance` and normalized to the same starting capital as the portfolio.

---

## plot_equity

```python
libb.plot_equity() -> None
```

Generate a single-line equity curve for the portfolio.

---

# Underlying Graph Functions

These functions can also be called directly if desired.

---

## Function: `plot_equity_and_sentiment`

### Purpose

Creates a two-panel plot:

- Top: Portfolio equity over time
- Bottom: Sentiment polarity over time

The portfolio timeline is authoritative.  
Sentiment data is left-joined on `date`.

Rows without sentiment values are dropped after merge.

---

### Inputs

#### Portfolio History (CSV)

Required columns:

- `date` — calendar date in `YYYY-MM-DD` format
- `equity` — total portfolio equity

Other columns may be present but are ignored.

---

#### Sentiment History (JSON)

Expected format:

- A JSON array
- Each element must contain:
  - `date` — calendar date in `YYYY-MM-DD` format
  - `polarity` — numeric sentiment polarity score

Example structure:

```json
[
  {"date": "2024-01-01", "polarity": 0.12},
  {"date": "2024-01-02", "polarity": -0.08}
]
```

---

### Plot Behavior

- Two vertically stacked subplots
- Shared x-axis
- Horizontal reference line at polarity = 0
- Grid enabled on both subplots
- Figure size: 10 x 6

---

## Function: `plot_equity`

### Purpose

Generate a single equity curve for the portfolio.

---

### Behavior

- Reads portfolio history CSV
- Uses first equity value as starting capital
- Plots equity over time
- Annotates final percentage return on the chart
- Displays legend and grid
- Figure size: 10 x 6
- Uses matplotlib style: `"seaborn-v0_8-whitegrid"`

---

## Function: `plot_equity_vs_baseline`

### Purpose

Compare portfolio performance to a benchmark ticker.

---

### Behavior

1. Reads portfolio history CSV.
2. Determines start and end dates.
3. Downloads baseline price data via `yfinance`.
4. Normalizes baseline to match portfolio starting capital.
5. Plots both time series.
6. Annotates final percentage returns for both lines.

---

### Baseline Normalization

The baseline is scaled using:

```
scaling_factor = starting_equity / baseline_start_price
```

This ensures both portfolio and baseline represent the value of the same initial capital investment.

---

### Inputs

#### Portfolio CSV

Required columns:

- `date`
- `equity`

---

#### Baseline Ticker

- Any ticker supported by Yahoo Finance.
- Default: `^SPX`

Examples:

- `"^SPX"` — S&P 500
- `"QQQ"` — Nasdaq 100 ETF
- `"SPY"` — S&P 500 ETF
- `"BTC-USD"` — Bitcoin

---

### Plot Behavior

- Two lines:
  - Portfolio (solid blue)
  - Baseline (orange dashed)
- Final percentage returns annotated
- Rotated date labels
- Grid enabled
- Figure size: 10 x 6
- Uses matplotlib style: `"seaborn-v0_8-whitegrid"`

---

# Notes & Limitations

- Graphs require valid portfolio history data.
- Sentiment plotting requires at least one overlapping sentiment record.
- Baseline comparison requires internet access (via `yfinance`).
- No statistical metrics are returned — this module is visualization-only.
- Missing or malformed data will raise standard pandas/matplotlib errors.

---

# Example Usage

Using model wrapper methods:

```python
from libb.model import LIBBmodel

libb = LIBBmodel("user_side/runs/run_v1/model_a")

libb.plot_equity()
libb.plot_equity_vs_baseline(baseline="^SPX")
libb.plot_equity_and_sentiment()
```