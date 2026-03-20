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

- `config` (`dict | None`, default: `None`)
  Optional configuration dictionary. If `None`, default values are used.
  See the Config section below for available keys and defaults.

---

## Config

LIBB accepts an optional `config` dict that controls experiment parameters.
If no config is passed, all values default as shown below.

```python
config = {
    "starting_cash": 10_000,        # Initial cash balance/metrics
    "risk_free_rate": 0.045,        # Annual risk-free rate used in Sharpe/Sortino
    "trading_days_per_year": 252,   # Used for annualizing metrics
    "slippage_pct_per_trade": 0.0,  # Slippage applied at fill time (e.g. 0.001 = 0.1%)
}
```

On first run, the config is written to `config.json` in the run directory.
On subsequent runs, the disk config is used unless the run is explicitly unlocked.

Once a config is written to disk it is locked by default, preventing accidental
overwrites mid-experiment. To allow a new config to overwrite the disk config,
set `"locked": false` in the on-disk `config.json`.

### Notes

- Partial configs are supported — omitted keys fall back to defaults.
- Invalid types for any key also fall back to defaults silently.

### Locking

Once a config is written to disk it is locked by default, preventing accidental
overwrites mid-experiment. To allow a new config to overwrite the disk config,
set `"locked": false` in the on-disk `config.json`.

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

The following examples are similar to `user_side/workflow.py` and represent
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
        config = {"starting_cash": 5_000, "slippage_pct_per_trade": 0.01}
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}", run_date=date, config=config)
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
        config = {"starting_cash": 10_000, "slippage_pct_per_trade": 0.01}
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}", run_date=date, config=config)
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
├── config.json               # run configuration and parameters
|
├── metrics/                  # evaluation outputs
|
|
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
