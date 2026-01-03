# Graphing


## Function: `plot_equity_and_sentiment`

### Purpose

Generate a single figure with two vertically aligned subplots:

- Top subplot: portfolio equity over time  
- Bottom subplot: sentiment polarity over time  

Both subplots share the same time axis.

---

## Inputs

### Portfolio History (CSV)

A CSV file path representing daily portfolio state.

Required columns:
- `date` — calendar date in `YYYY-MM-DD` format
- `equity` — total portfolio equity for the day

Additional columns (e.g., returns, benchmark equity) may be present but are ignored by this function.

---

### Sentiment History (JSON)

A JSON file path containing sentiment records derived from model outputs.

Expected format:
- a list of JSON objects
- each object must contain:
  - `date` — calendar date in `YYYY-MM-DD` format
  - `polarity` — sentiment polarity score

## Example 

This example assumes there is existing valid data already in the files.

```python
from libb.model import LIBBmodel
from libb.graphs.sentiment import plot_equity_and_sentiment

libb = LIBBmodel(f"user_side/runs/run_v1/{model}")
plot_equity_and_sentiment(libb._portfolio_history_path, libb._sentiment_path)
```
