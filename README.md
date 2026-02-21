# LLM Investor Behavior Benchmark (LIBB)

## What Is LIBB?

LIBB is an open-source, opinionated research library designed to automatically manage portfolio state and compute key metrics,
while still giving users flexibility over the system.

## Why LIBB Exists

This project originally began as a generic benchmark for LLM-based trading in U.S. equities. While surveying existing LLM trading projects (including my own), I noticed a consistent lack of rigorous sentiment, behavioral, and performance metrics; most projects reported little more than an equity curve.

This raised a fundamental question: ***“Why isn’t LLM trading held to the same analytical standards as the rest of finance?”***

So I developed a library designed to support rigorous evaluation of LLM-driven trading systems. The long-term goal is to provide a shared foundation for this work and, ultimately, to establish a community standard for this type of research.

## Features

- **Persistent Portfolio State**  
  All portfolio data is explicitly stored on disk, enabling inspection,
  reproducibility, and post-hoc analysis across runs.

- **Sentiment Analysis**  
  Built-in support for sentiment analysis, with results persisted as
  first-class research artifacts.

- **Performance Metrics**  
  Calculation of key performance evaluation metrics (Sharpe, Sortino, Drawdown, R², etc.)
  based on the first day of portfolio activity. Behavioral analytics is still being developed.

- **Reproducible Run Structure**  
  Each model run follows a consistent on-disk directory layout, making
  experiments easy to reproduce, compare, and archive.

- **Flexible Execution Workflows**  
  Execution logic remains fully user-controlled, allowing researchers
  to integrate custom strategies, models, or data sources.

## How It Works

LIBB operates as a file-backed execution loop where portfolio state,
analytics, and research artifacts are explicitly persisted to disk.

For each run, the engine:

1. Loads and processes existing portfolio state
2. Recieves inputs (e.g., via an LLM)
3. Computes and stores analytical signals (such as sentiment) via explicit user calls
4. saves execution instructions (orders) by passing JSON block
5. Persists all outputs for inspection and reuse

Execution scheduling (e.g., daily vs. weekly runs) and model orchestration
are intentionally left to the user, preserving flexibility while
maintaining a consistent on-disk state.

## Documentation

New to LIBB?  
Start here → **[Documentation Guide](docs/README.md)**

This guide explains the system philosophy, execution workflow,
and how to read the codebase effectively.

---

## Example Workflow

```python

from libb import LIBBmodel
from .prompt_orchestration.prompt_models import prompt_daily_report
from libb.other.parse import parse_json
import pandas as pd

MODELS = ["deepseek", "gpt-4.1"]

def daily_flow():
    for model in MODELS:
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}")
        libb.process_portfolio()

        daily_report = prompt_daily_report(libb)

        libb.save_daily_update(daily_report)

        orders_json = parse_json(daily_report, "ORDERS_JSON")
        libb.save_orders(orders_json)

        libb.analyze_sentiment(daily_report, report_type="daily")

    return
```

---

## What Gets Created Automatically

- Run directory structure
- Portfolio files
- Metrics files

No manual file setup is required.

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

## Getting Started

This guide shows two supported setup paths:

- **Option A (Recommended): Virtual Environment**
- **Option B: Global / No Virtual Environment**

Choose the option that best fits your workflow.

---

## Option A: Virtual Environment (Recommended)

This option isolates dependencies and avoids conflicts with other Python projects.

### 1. Clone the Repository

```bash
git clone https://github.com/LuckyOne7777/LLM-Investor-Behavior-Benchmark.git
cd LLM-Investor-Behavior-Benchmark
```

Verify contents:

```bash
ls
```

You should see folders like libb/, user_side/, and requirements.txt.

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv .venv
```

macOS / Linux:

```bash

python3 -m venv .venv

```

### 3. Activate the Virtual Environment

Windows (PowerShell)
If activation fails due to script execution policy, run once:

```bash
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then activate:

```bash
.venv\Scripts\activate
```

Windows (Command Prompt alternative)

```bash
.venv\Scripts\activate.bat
```

macOS / Linux

```bash
source .venv/bin/activate
```

Verify activation:

```bash
python --version
```

You should see (.venv) in your shell prompt.

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 5. Verify Installation

```bash
python -c "import libb; print(libb.__file__)"
```

Expected output should point to `libb/__init__.py`.

### 6. Set Environment Variables

macOS / Linux:

```bash
export OPENAI_API_KEY="your_key_here"
export DEEPSEEK_API_KEY="your_key_here"
```

Windows (PowerShell):

```bash
setx OPENAI_API_KEY "your_key_here"
setx DEEPSEEK_API_KEY "your_key_here"
```

Restart the terminal after using setx.

### 7. Run an Example Workflow

```bash
python -m user_side.workflow
```

### 8. Exit the Virtual Environment

Deactivate:

To remove the virtual environment entirely:

Linux / macOS:

```bash
rm -rf .venv
```

Windows:

```bash
Remove-Item -Recurse -Force .venv
```

## Option B: Global Setup (No Virtual Environment)

This option installs dependencies into the active Python environment.
Recommended only for users comfortable managing global Python packages.

### 1. Clone the Repo

```bash
git clone https://github.com/LuckyOne7777/LLM-Investor-Behavior-Benchmark.git
cd LLM-Investor-Behavior-Benchmark
```

### 2. Verify Python Version

LIBB requires Python 3.10 or newer.

```bash
python --version
```

### 3. Upgrade pip

```bash
python -m pip install --upgrade pip
```

### 4. Install Dependencies Globally

```bash
pip install -r requirements.txt
pip install -e .
```

Verify installation:

```bash

python -c "import libb; print(libb.__file__)"
```

### 5. Set Environment Variables

Same as Option A.

### 6. Run an Example Workflow

```bash
python -m user_side.workflow
```

---

### Optional: Uninstall

```bash
pip uninstall libb
```

Notes

Dependencies may remain installed if they were already present.

Windows users may encounter PowerShell execution policy restrictions.

Command Prompt can be used instead of PowerShell if preferred.

Execution scheduling and orchestration are intentionally left to the user.

---

## Research Directions

LIBB is an exploratory research library, and its development is driven
by ongoing areas of improvement rather than a fixed roadmap.

Areas of current interest include:

- Deeper integration of performance analytics into the core workflow
- Behavioral analysis derived from trading decisions and execution patterns
- Expansion of sentiment analytics across multiple data sources
- Improved tooling for comparing runs and strategies over time
- General design improvements for efficiency and code quality

To see the current roadmap for major features, check out: [roadmap.md](docs/short-term-roadmap.md)

These directions reflect current research interests and may evolve,
change, or be abandoned as the project develops.
