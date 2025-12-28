# Workflow

This section describes the canonical way to use LIBB in a research or live-tracking environment.

LIBB is designed to be explicit and procedural:
- No critical logic runs implicitly
- Users control when processing, prompting, and saving occur
- The workflow is identical for single-model and multi-model runs

All examples below are taken from the `user_side/` folder.  
You are encouraged to copy them directly or adapt them as needed.
Please read the entire file to fully understand risks and required elements.

---

## Core Workflow Philosophy

Every LIBB workflow follows the same high-level pattern:

1. Initialize a `LIBBmodel` with a run directory
2. **Process the portfolio first (required)**
3. Generate model output via prompts
4. Parse structured outputs (JSON blocks)
5. Save results and artifacts
6. (Optional) Run auxiliary analysis (sentiment, metrics, etc.)

The only hard requirement is that `process_portfolio()` must be called before
any prompts are executed. All downstream logic depends on this processed state.

---

## Required Components

A minimal workflow requires:

- Prompt skeletons (e.g. daily / weekly research prompts)
- User-defined functions for executing prompts
- Awareness of design limitations listed in `important-notes.md`

---

## Minimum Required Workflow

```python
MODELS = ["deepseek", "gpt-4.1"]

def weekly_flow():
for model in MODELS:
libb = LIBBmodel(f"user_side/runs/run_v1/{model}")

    # Required: must always run first
    libb.process_portfolio()

    deep_research_report = prompt_deep_research(libb)

    orders_json = parse_json(deep_research_report, "ORDERS_JSON")
    libb.save_orders(orders_json)
return
```
---

## Example Workflow

The following examples are taken from `user_side/workflow.py` and represent
recommended usage patterns.

---

### Weekly Workflow

```python
from libb.model import LIBBmodel
from .prompt_models import prompt_daily_report, prompt_deep_research
from libb.other.parse import parse_json

MODELS = ["deepseek", "gpt-4.1"]

def weekly_flow():
for model in MODELS:
libb = LIBBmodel(f"user_side/runs/run_v1/{model}")
    # Required: initialize processed state
    libb.process_portfolio()

    deep_research_report = prompt_deep_research(libb)

    # Optional persistence
    libb.save_deep_research(deep_research_report)

    orders_json = parse_json(deep_research_report, "ORDERS_JSON")
    libb.save_orders(orders_json)

    # Optional post-processing
    libb.analyze_sentiment(deep_research_report)
return
```
---
### Daily Workflow

```python
def daily_flow():
for model in MODELS:
libb = LIBBmodel(f"user_side/runs/run_v1/{model}")

    # Required
    libb.process_portfolio()

    daily_report = prompt_daily_report(libb)

    libb.analyze_sentiment(daily_report)
    libb.save_daily_update(daily_report)

    orders_json = parse_json(daily_report, "ORDERS_JSON")
    libb.save_orders(orders_json)
return
```

## Notes

- `process_portfolio()` is intentionally explicit and must never be called implicitly
- do not use any other functions besides `process_portfolio()` for processing
- Constructors do not perform processing or side effects
- Users are free to extend or reorder optional steps, but processing must occur first
- The workflow is designed for reproducibility and auditability
