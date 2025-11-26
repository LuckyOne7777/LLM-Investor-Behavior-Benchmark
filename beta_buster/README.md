# Beta Buster

Beta Buster is a minimal open-source benchmark for daily AI trading experiments. This MVP tracks portfolio performance for separate divisions (stock universes) and updates their leaderboards automatically.

## Divisions included
- **Microcap**: market cap below $300M.
- **Midcap**: market cap between $2B and $10B.

Each division lives under `divisions/` and contains:
- `portfolio.csv`: portfolio state with cash and positions.
- `leaderboard.csv`: daily portfolio snapshots.
- `rules.json`: metadata describing the division constraints.

## How it works
- `update_all.py` loads every division, pulls prices from Yahoo Finance, computes portfolio value, and appends a new daily row to each leaderboard.

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
A GitHub Actions workflow (`.github/workflows/update.yml`) runs daily after market close. It installs dependencies, runs `update_all.py`, and commits any changed CSV files back to the repo.
