# Workflow

This section describes the canonical way to use LIBB in research or live-tracking environments.

LIBB is explicit and procedural by design:
- No critical logic runs implicitly
- All file handling is deterministic and setup automatically
- Users control when processing, prompting, and persistence occur
- The workflow is identical for single-model and multi-model runs

All examples below are taken from `user_side/` and represent recommended usage patterns.

## Core Workflow

Every LIBB workflow follows the same high-level sequence:

1. Initialize a `LIBBmodel` with a run directory
2. Process the portfolio (**required**)
3. Generate model output via prompts
4. Parse structured outputs (JSON blocks)
5. Save results and artifacts
6. (Optional) Run auxiliary analysis (sentiment, metrics, etc.)

**Invariant:**  
`process_portfolio()` must be called before any prompts are executed.  
All downstream logic depends on this processed state.

## Required Components

A minimal workflow requires:
- Prompt skeletons (e.g. daily or weekly research prompts)
- User-defined functions for executing prompts
- Familiarity with constraints listed in `important-notes.md`
- API keys set for `OPENAI_API_KEY` and `DEEPSEEK_API_KEY`

---

## Behavio Parameters

The following parameters affect the behavior of a LIBB run:

- `date` (`str | date`, default: current system date)  
  Overrides the run date used by the model.  
  Useful for reproducing historical executions or evaluating behavior at a specific point in time.

- `starting_cash` (`float`, default: `10_000`)  
  Initial cash balance used when initializing a portfolio.  
  Can be overridden to simulate different account sizes.
  Changing starting cash value in after intial creation is not recommended.

---

## Minimum Required Workflow

```python

from libb.model import LIBBmodel
from libb.other.parse import parse_json # or another parsing function

def workflow():
  libb = LIBBmodel(f"some_folder/model-x")

  # Required: must always run first
  libb.process_portfolio()

  # user created function
  report = prompt_model()

  orders_json = parse_json(eport, "ORDERS_JSON")
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
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}", date="2025-12-15", STARTING_CASH=30_000)
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

        libb.process_portfolio()

        daily_report = prompt_daily_report(libb)

        libb.analyze_sentiment(daily_report)
        libb.save_daily_update(daily_report)

        orders_json = parse_json(daily_report, "ORDERS_JSON")
        libb.save_orders(orders_json)
    return
```

---

## Created File Tree

After running for the first time, LIBB generates a fixed directory structure at the user-specified output path.

```
<output_dir>/
├── metrics/          # evaluation
│   ├── behavior.json
│   ├── performance.json
│   └── sentiment.json
├── portfolio/        # trading state & history
│   ├── pending_trades.json
│   ├── portfolio.csv
│   ├── portfolio_history.csv
│   ├── position_history.csv
│   └── trade_log.csv
└── research/         # generated analysis
    ├── daily_reports/
    └── deep_research/

```

LIBB will use this file tree to save artifacts for all future runs in the output directory.

---



## Notes

- do not use any other functions besides `process_portfolio()` for processing
- Constructors do not perform processing or side effects
- The workflow is designed for reproducibility and auditability
