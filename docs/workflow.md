# Workflow

This section describes the canonical way to use LIBB in research or live-tracking environments.

LIBB is explicit and procedural by design:

- No critical logic runs implicitly
- All file handling is deterministic and set up automatically
- Users control when processing, prompting, and persistence occur
- The workflow is identical for single-model and multi-model runs

## Core Workflow

Every LIBB workflow follows the same high-level sequence:

1. Initialize a `LIBBmodel` with a run directory
2. Process the portfolio (**required**)
3. Generate model output via prompts
4. Parse structured outputs (JSON blocks)
5. Save results and artifacts
6. (Optional) Run auxiliary analysis (sentiment, performance, behavior metrics)

**Invariant:**
`process_portfolio()` must be called before any prompts are executed.
All downstream logic depends on this processed state.

## Required Components

A minimal workflow requires:

- Prompt skeletons (e.g. daily or weekly research prompts)
- User-defined functions for executing prompts
- Familiarity with constraints listed in `important-constraints.md`
- API keys set for `OPENAI_API_KEY` and `DEEPSEEK_API_KEY`

---

## Behavioral Parameters

The following parameters affect the behavior of a LIBB run:

- `run_date` (`str | date`, default: current system date)
  Overrides the run date used by the model.
  Useful for reproducing historical executions or evaluating behavior at a specific point in time.

- `starting_cash` (`float`, default: `10_000`)
  Initial cash balance used when initializing a portfolio.
  Can be overridden to simulate different account sizes.
  Changing starting cash after initial creation is not recommended.

---

## Minimum Required Workflow

```python
from libb import LIBBmodel
from libb.other.parse import parse_json

def workflow():
    libb = LIBBmodel("some_folder/model-x")

    # Required: must always run first
    libb.process_portfolio()

    # User-defined function — replace with whatever prompting logic you use
    report = prompt_model(libb)

    orders_json = parse_json(report, "ORDERS_JSON")
    libb.save_orders(orders_json)
    return
```

`prompt_model` is a placeholder. Users are responsible for writing their own
prompting functions. See `user_side/prompt_orchestration/prompt_models.py` for
an example implementation.

---

## Example Workflows

The following examples are taken from `user_side/workflow.py` and represent
recommended usage patterns.

---

### Weekly Workflow

```python
from libb import LIBBmodel
from .prompt_orchestration.prompt_models import prompt_daily_report, prompt_deep_research
from libb.other.parse import parse_json
import pandas as pd

MODELS = ["deepseek", "gpt-4.1"]

def weekly_flow(date):
    for model in MODELS:
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}", run_date=date)
        libb.process_portfolio()

        deep_research_report = prompt_deep_research(libb)

        # Optional persistence
        libb.save_deep_research(deep_research_report)

        orders_json = parse_json(deep_research_report, "ORDERS_JSON")
        libb.save_orders(orders_json)

        # Optional post-processing
        libb.analyze_sentiment(deep_research_report, report_type="Deep_Research")
    return
```

---

### Daily Workflow

```python
def daily_flow(date):
    for model in MODELS:
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}", run_date=date)
        libb.process_portfolio()

        daily_report = prompt_daily_report(libb)

        libb.save_daily_update(daily_report)

        orders_json = parse_json(daily_report, "ORDERS_JSON")
        libb.save_orders(orders_json)

        libb.analyze_sentiment(daily_report, report_type="Daily")
    return
```

---

### Optional Metrics

After any workflow, behavioral and performance metrics can be generated
independently:

```python
# Generate all metrics for a completed run
libb.generate_performance_metrics(baseline_ticker="^SPX")
libb.generate_behavior_metrics()
```

These are not required as part of the daily or weekly loop and can be
called at any point after `process_portfolio()` has been run at least once
and the relevant CSV files are non-empty.

---

## Created File Tree

After running for the first time, LIBB generates a fixed directory structure at the user-specified output path.

```text
<output_dir>/
├── metrics/                  # evaluation outputs
│   ├── behavior.json
│   ├── performance.json
│   └── sentiment.json
│
├── portfolio/                # live trading state & history
│   ├── cash.json             # authoritative current cash balance
│   ├── pending_trades.json
│   ├── portfolio.csv         # current positions only
│   ├── portfolio_history.csv # daily equity & cash snapshots
│   ├── position_history.csv  # per-position daily history
│   └── trade_log.csv
│
├── logging/                  # per-run execution logs (JSON)
│
└── research/                 # generated analysis & reports
    ├── daily_reports/
    └── deep_research/
```

LIBB will use this file tree to save artifacts for all future runs in the output directory.

---

## Notes

- Do not call internal processing methods like `_process()` directly.
  Only `process_portfolio()` should be used for processing — it includes
  safety checks, rollback logic, and NYSE calendar validation that the
  internal methods do not.
- Constructors do not perform processing or side effects
- The workflow is designed for reproducibility and auditability
