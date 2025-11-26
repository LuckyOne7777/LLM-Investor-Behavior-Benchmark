"""Update all Beta Buster divisions with dual portfolios.

For each division this script now manages two independent portfolios:
- Baseline portfolio: tracks the benchmark with no trades.
- LLM portfolio: executes the configured GPT-driven strategy.

The design is resilient to missing files and future model additions so daily
GitHub Actions runs do not fail due to missing artifacts.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf

from baseline import BaselineState, compute_baseline_value, ensure_baseline, fetch_latest_price
from strategy import load_rules, run_strategy
from utils import (
    ensure_leaderboard_csv,
    ensure_portfolio_csv,
    list_divisions,
    load_portfolio,
    save_portfolio,
)

# Configure basic logging for visibility when running from automation
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Root folders
BASE_DIR = Path(__file__).parent
DIVISIONS_DIR = BASE_DIR / "divisions"


# ---------------------------------------------------------------------------
# Price helpers
# ---------------------------------------------------------------------------

def fetch_prices(symbols: Dict[str, float]) -> Dict[str, float]:
    """Fetch latest close prices for provided tickers using yfinance."""

    tickers = [ticker for ticker in symbols.keys() if ticker]
    if not tickers:
        return {}

    prices: Dict[str, float] = {}
    try:
        data = yf.download(tickers=tickers, period="2d", progress=False, auto_adjust=False)
        if len(tickers) == 1:
            close_series = data["Close"]
            price = float(close_series.iloc[-1])
            prices[tickers[0]] = price
        else:
            close_series = data["Close"].iloc[-1]
            for ticker in tickers:
                try:
                    prices[ticker] = float(close_series[ticker])
                except Exception as exc:  # noqa: BLE001
                    logging.error("Could not fetch price for %s: %s", ticker, exc)
    except Exception as exc:  # noqa: BLE001
        logging.error("Price download failed: %s", exc)

    return prices


def calculate_portfolio_value(cash: float, positions: Dict[str, float], prices: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Compute the total portfolio value and position market values."""

    position_values: Dict[str, float] = {}
    total_value = cash

    for ticker, shares in positions.items():
        price = prices.get(ticker)
        if price is None:
            logging.warning("Missing price for %s, skipping its value.", ticker)
            continue
        position_values[ticker] = shares * price
        total_value += position_values[ticker]

    return total_value, position_values


# ---------------------------------------------------------------------------
# Division processing
# ---------------------------------------------------------------------------

def ensure_division_files(division_path: Path) -> None:
    """Ensure all required files exist for a division."""

    ensure_portfolio_csv(division_path / "portfolio_baseline.csv")
    ensure_portfolio_csv(division_path / "portfolio_llm.csv")
    ensure_leaderboard_csv(division_path / "leaderboard_baseline.csv")
    ensure_leaderboard_csv(division_path / "leaderboard_llm.csv")


def prepare_baseline(
    division_path: Path, rules: Dict[str, object], baseline_portfolio: Dict[str, object]
) -> Tuple[BaselineState, float]:
    """Load or create baseline exposure and fetch the current benchmark price."""

    benchmark_ticker = str(rules.get("benchmark", "")).strip()
    baseline_path = division_path / "baseline.json"
    baseline_state = ensure_baseline(baseline_path, benchmark_ticker, baseline_portfolio.get("cash", 0.0))
    benchmark_price = fetch_latest_price(benchmark_ticker) or 0.0
    return baseline_state, benchmark_price


def append_leaderboard(leaderboard_path: Path, row: Dict[str, object]) -> None:
    """Append a single row to the leaderboard, preserving column order."""

    ensure_leaderboard_csv(leaderboard_path)
    df = pd.read_csv(leaderboard_path)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    columns = ["date", "portfolio_value", "benchmark_value", "alpha", "cash", "positions_json"]
    df = df[columns]
    df.to_csv(leaderboard_path, index=False)


def process_portfolio(
    division_path: Path,
    portfolio_path: Path,
    leaderboard_path: Path,
    rules: Dict[str, object],
    baseline_value: float,
    strategy_override: str,
    leaderboard_context: List[Dict[str, object]],
    benchmark_ticker: str,
    baseline_units: float,
) -> None:
    """Process a single portfolio type (baseline or llm)."""

    portfolio = load_portfolio(portfolio_path)
    logging.info("  Processing %s", portfolio_path.name)

    # Force the correct model type per portfolio
    rules_for_strategy = dict(rules)
    rules_for_strategy["model_type"] = strategy_override

    # For the baseline portfolio, mirror the benchmark exposure
    if strategy_override == "baseline" and benchmark_ticker:
        portfolio["positions"] = {benchmark_ticker: baseline_units}
        portfolio["cash"] = 0.0

    # Collect context rows for strategies
    context_rows = leaderboard_context[-3:]

    updated_portfolio = run_strategy(portfolio, rules_for_strategy, context_rows)
    save_portfolio(portfolio_path, updated_portfolio)

    prices = fetch_prices(updated_portfolio.get("positions", {}))
    total_value, _ = calculate_portfolio_value(
        float(updated_portfolio.get("cash", 0.0)),
        updated_portfolio.get("positions", {}),
        prices,
    )

    alpha = total_value - baseline_value
    row = {
        "date": dt.date.today().isoformat(),
        "portfolio_value": round(total_value, 2),
        "benchmark_value": round(baseline_value, 2),
        "alpha": round(alpha, 2),
        "cash": round(float(updated_portfolio.get("cash", 0.0)), 2),
        "positions_json": json.dumps(updated_portfolio.get("positions", {})),
    }
    append_leaderboard(leaderboard_path, row)


def update_division(division_path: Path) -> None:
    """Process a single division safely."""

    logging.info("Updating division: %s", division_path.name)

    try:
        ensure_division_files(division_path)
        rules_path = division_path / "rules.json"
        rules = load_rules(rules_path)

        baseline_portfolio_path = division_path / "portfolio_baseline.csv"
        llm_portfolio_path = division_path / "portfolio_llm.csv"
        baseline_leaderboard_path = division_path / "leaderboard_baseline.csv"
        llm_leaderboard_path = division_path / "leaderboard_llm.csv"

        baseline_portfolio = load_portfolio(baseline_portfolio_path)
        baseline_state, benchmark_price = prepare_baseline(division_path, rules, baseline_portfolio)
        benchmark_value = compute_baseline_value(baseline_state, benchmark_price) if benchmark_price else 0.0

        # Load leaderboard context for strategies
        baseline_lb_rows = pd.read_csv(baseline_leaderboard_path).to_dict(orient="records") if baseline_leaderboard_path.exists() else []
        llm_lb_rows = pd.read_csv(llm_leaderboard_path).to_dict(orient="records") if llm_leaderboard_path.exists() else []

        # Process baseline portfolio
        process_portfolio(
            division_path,
            baseline_portfolio_path,
            baseline_leaderboard_path,
            rules,
            benchmark_value,
            "baseline",
            baseline_lb_rows,
            str(rules.get("benchmark", "")).strip(),
            baseline_state.units,
        )

        # Process LLM portfolio
        llm_portfolio = load_portfolio(llm_portfolio_path)
        process_portfolio(
            division_path,
            llm_portfolio_path,
            llm_leaderboard_path,
            rules,
            benchmark_value,
            "llm",
            llm_lb_rows,
            str(rules.get("benchmark", "")).strip(),
            baseline_state.units,
        )

        logging.info("Finished division %s", division_path.name)
    except Exception as exc:  # noqa: BLE001
        logging.error("Division %s failed: %s", division_path.name, exc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Load all divisions and update their leaderboards."""

    logging.info("Starting Beta Buster update")

    divisions = list_divisions(DIVISIONS_DIR)
    if not divisions:
        logging.warning("No divisions found under %s", DIVISIONS_DIR)
        return

    for division in divisions:
        update_division(division)

    logging.info("All divisions processed")


if __name__ == "__main__":
    main()

