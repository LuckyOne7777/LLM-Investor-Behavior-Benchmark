# Beta Buster

Beta Buster is an automated AI trading benchmark. Each division represents a market universe and runs multiple independent trading models (OpenAI, DeepSeek, Gemini, etc.) head to head against the same benchmark index. All portfolios update daily using GitHub Actions.

Beta Buster is designed for simplicity, reliability, and extensibility. New models and new divisions can be added without modifying core logic.

## Features

- Multiple AI models per division.
- Baseline benchmark tracking for every division.
- Automatic daily updates via GitHub Actions.
- Price data from Yahoo Finance.
- Robust file handling. Missing files are created automatically.
- Modular strategy system with provider-specific logic.
- All state stored in CSV and JSON files.

## How It Works

Each division contains:

1. A baseline portfolio that tracks the benchmark index using scaled units.
2. One portfolio per AI model listed in division_models.json.
3. A leaderboard CSV for each portfolio.
4. A rules.json file that defines the division's market universe and benchmark.

Daily update cycle:

1. Fetch latest prices for all held tickers.
2. Update the baseline benchmark value.
3. For each model:
   - Build a prompt including the portfolio, rules, and recent leaderboard rows.
   - Call the model provider's API.
   - Parse the model's JSON trade instruction.
   - Apply buy, sell, or hold.
4. Save updated portfolios back to disk.
5. Append a new row to each leaderboard.

## File Structure
```
beta_buster/
    update_all.py
    strategy.py
    baseline.py
    utils.py
    division_models.json
    divisions/
        microcap/
            rules.json
            baseline.json
            portfolio_baseline.csv
            leaderboard_baseline.csv
            portfolio_openai.csv
            leaderboard_openai.csv
            portfolio_deepseek.csv
            leaderboard_deepseek.csv
        midcap/
            rules.json
            baseline.json
            portfolio_baseline.csv
            leaderboard_baseline.csv
            portfolio_openai.csv
            leaderboard_openai.csv
```
## Division Configuration (rules.json)

Each division contains a simple rules.json file defining the market universe and benchmark. Models are not defined here.

Example:
```
{
  "name": "Microcap Division",
  "market_cap_max": 300000000,
  "benchmark": "IWM"
}
```
## Global Model Configuration (division_models.json)

All AI traders are defined globally in division_models.json.

Example:
```
{
  "models": [
    {
      "id": "openai",
      "model_type": "openai",
      "model_name": "gpt-5.1"
    },
    {
      "id": "deepseek",
      "model_type": "deepseek",
      "model_name": "deepseek-chat"
    },
    {
      "id": "gemini",
      "model_type": "gemini",
      "model_name": "gemini-2.5-flash"
    }
  ]
}
```
Each model creates its own portfolio and leaderboard inside every division.

## Running the Updater Manually

Install requirements:
```bash
pip install -r requirements.txt
```
Run the updater:

python update_all.py

## Automation

A GitHub Actions workflow runs update_all.py daily after market close. It installs dependencies, executes the updater, and commits any changed CSV files back to the repository.
