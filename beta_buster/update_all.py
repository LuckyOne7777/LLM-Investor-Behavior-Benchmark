"""
Update all Beta Buster divisions with unlimited AI traders.

Each division now contains:
- Baseline (benchmark tracker)
- N AI trader portfolios defined in division_models.json
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, List

import pandas as pd
import yfinance as yf

from baseline import BaselineState, compute_baseline_value, ensure_baseline, fetch_latest_price
from strategy import run_strategy, load_rules
from utils import (
    ensure_generic_portfolio,
    ensure_generic_leaderboard,
    load_json,
    load_portfolio,
    save_portfolio,
    list_divisions
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = Path(__file__).parent
DIVISIONS_DIR = BASE_DIR / "divisions"
MODELS_PATH = BASE_DIR / "division_models.json"


def fetch_prices(symbols: Dict[str, float]) -> Dict[str, float]:
    if not symbols:
        return {}

    tickers = list(symbols.keys())
    prices = {}
    try:
        data = yf.download(tickers=tickers, period="2d", progress=False, auto_adjust=False)
        if len(tickers) == 1:
            close_series = data["Close"]
            prices[tickers[0]] = float(close_series.iloc[-1])
        else:
            close_series = data["Close"].iloc[-1]
            for ticker in tickers:
                try:
                    prices[ticker] = float(close_series[ticker])
                except:
                    pass
    except:
        pass

    return prices


def calculate_portfolio_value(cash: float, positions: Dict[str, float], prices: Dict[str, float]) -> float:
    total = cash
    for t, s in positions.items():
        if t in prices:
            total += s * prices[t]
    return total


def process_single_portfolio(
    division_path: Path,
    rules: Dict[str, object],
    model_id: str,
    model_type: str,
    model_name: str,
    baseline_value: float,
    baseline_units: float,
    benchmark_ticker: str,
    leaderboard_context: List[Dict[str, object]]
):
    portfolio_path = division_path / f"portfolio_{model_id}.csv"
    leaderboard_path = division_path / f"leaderboard_{model_id}.csv"

    ensure_generic_portfolio(portfolio_path)
    ensure_generic_leaderboard(leaderboard_path)

    portfolio = load_portfolio(portfolio_path)

    # Override model type/name directly
    strategy_rules = dict(rules)
    strategy_rules["model_type"] = model_type
    strategy_rules["model_name"] = model_name

    # Run model
    updated = run_strategy(portfolio, strategy_rules, leaderboard_context)
    save_portfolio(portfolio_path, updated)

    # Value
    prices = fetch_prices(updated.get("positions", {}))
    total_value = calculate_portfolio_value(updated["cash"], updated["positions"], prices)

    alpha = total_value - baseline_value

    row = {
        "date": dt.date.today().isoformat(),
        "portfolio_value": round(total_value, 2),
        "benchmark_value": round(baseline_value, 2),
        "alpha": round(alpha, 2),
        "cash": round(updated["cash"], 2),
        "positions_json": json.dumps(updated["positions"])
    }

    df = pd.read_csv(leaderboard_path)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(leaderboard_path, index=False)


def update_division(division_path: Path, model_specs: List[Dict[str, object]]):
    logging.info(f"Updating division: {division_path.name}")

    rules = load_rules(division_path / "rules.json")
    benchmark = str(rules.get("benchmark", "")).strip()

    # Baseline
    baseline_portfolio_path = division_path / "portfolio_baseline.csv"
    baseline_leaderboard_path = division_path / "leaderboard_baseline.csv"

    ensure_generic_portfolio(baseline_portfolio_path)
    ensure_generic_leaderboard(baseline_leaderboard_path)

    baseline_portfolio = load_portfolio(baseline_portfolio_path)

    baseline_state = ensure_baseline(
        division_path / "baseline.json",
        benchmark,
        baseline_portfolio["cash"]
    )
    benchmark_price = fetch_latest_price(benchmark) or 0.0
    baseline_value = compute_baseline_value(baseline_state, benchmark_price)

    # Read existing context rows
    baseline_context = pd.read_csv(baseline_leaderboard_path).to_dict(orient="records") if baseline_leaderboard_path.exists() else []

    # Force baseline positions
    baseline_portfolio["positions"] = {benchmark: baseline_state.units}
    baseline_portfolio["cash"] = 0.0
    save_portfolio(baseline_portfolio_path, baseline_portfolio)

    # Re-value baseline
    prices = fetch_prices(baseline_portfolio["positions"])
    baseline_portfolio_value = calculate_portfolio_value(0.0, baseline_portfolio["positions"], prices)

    # Append baseline leaderboard row
    baseline_row = {
        "date": dt.date.today().isoformat(),
        "portfolio_value": round(baseline_portfolio_value, 2),
        "benchmark_value": round(baseline_value, 2),
        "alpha": round(baseline_portfolio_value - baseline_value, 2),
        "cash": 0.0,
        "positions_json": json.dumps(baseline_portfolio["positions"])
    }
    df = pd.read_csv(baseline_leaderboard_path)
    df = pd.concat([df, pd.DataFrame([baseline_row])], ignore_index=True)
    df.to_csv(baseline_leaderboard_path, index=False)

    # Run N models
    for model in model_specs:
        process_single_portfolio(
            division_path,
            rules,
            model["id"],
            model["model_type"],
            model["model_name"],
            baseline_value,
            baseline_state.units,
            benchmark,
            baseline_context
        )


def main():
    model_config = load_json(MODELS_PATH)
    model_specs = model_config.get("models", [])

    divisions = list_divisions(DIVISIONS_DIR)
    for d in divisions:
        update_division(d, model_specs)


if __name__ == "__main__":
    main()
