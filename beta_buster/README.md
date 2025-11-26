
# Beta Buster

Beta Buster is a minimal open-source benchmark for daily AI trading experiments.
This MVP tracks portfolio performance for separate divisions (stock universes)
and updates their leaderboards automatically.

## Divisions included
- **Microcap**: market cap below $300M.
- **Midcap**: market cap between $2B and $10B.

Each division lives under `divisions/` and now contains separate portfolio and
leaderboard files for each trading model.

## How it works
- `update_all.py` loads every division, pulls prices from Yahoo Finance, updates
  two independent portfolios (baseline and LLM), and appends a new daily row to
  each leaderboard.
- The updater automatically creates any missing files so GitHub Actions can run
  reliably without manual intervention.

## Supported model types today
- `baseline`
- `llm`
- `rule_based` (placeholder for future expansion)

## How to add new trading models
1. Add or update `model_type` in the division's `rules.json` (e.g.
   `"model_type": "rule_based"`).
2. Implement a new function in `strategy.py` that performs the strategy logic.
   Use the existing `run_llm_strategy` and `run_rule_based_strategy` as
   templates for structure and error handling.
3. Register the new strategy in `run_strategy()` by adding another branch that
   dispatches to your function.
4. Extend `rules.json` with any additional fields your strategy needs.
5. If the new model requires extra packages, add them to `requirements.txt` so
   GitHub Actions can install them automatically.

## Division folder structure
Each division folder under `divisions/` should contain:

```
rules.json
baseline.json
portfolio_baseline.csv
leaderboard_baseline.csv
portfolio_llm.csv
leaderboard_llm.csv
```

## How to create a new division from scratch
1. Create a new directory under `divisions/` (e.g., `divisions/new_division`).
2. Add a `rules.json` file with at least a `benchmark` ticker and
   `model_type`. Example:
   ```json
   {
     "name": "New Division",
     "benchmark": "SPY",
     "model_type": "llm",
     "model_name": "gpt-4o-mini"
   }
   ```
3. Run `python update_all.py`. The script will automatically create the
   baseline/LLM portfolio and leaderboard CSV files plus `baseline.json` if they
   are missing.

## Safe automatic file creation
- `update_all.py` calls helpers in `utils.py` to ensure every required file is
  present. Missing CSVs are created with default cash and empty positions, while
  missing leaderboards are created with the correct columns.
- `baseline.json` is automatically initialized using the division's benchmark
  price and starting cash, storing scaled benchmark units that track the
  benchmark over time.

## Quickstart
1. Create a Python environment and install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the updater:
   ```bash
   python update_all.py
   ```

## Automation
A GitHub Actions workflow (`.github/workflows/update.yml`) runs daily after
market close. It installs dependencies, runs `update_all.py`, and commits any
changed CSV files back to the repo.
