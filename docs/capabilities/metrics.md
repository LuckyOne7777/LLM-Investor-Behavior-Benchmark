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
