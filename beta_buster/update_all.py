"""Update all Beta Buster divisions.

This script loads every division under `divisions/`, downloads current prices
from Yahoo Finance, calculates portfolio values, and appends a new row to each
leaderboard. Functions are intentionally small and heavily commented to stay
beginner-friendly.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import yfinance as yf

from strategy import load_rules, run_strategy
from utils import append_leaderboard_row, init_leaderboard, list_divisions, load_portfolio, save_portfolio

# Configure basic logging for visibility when running from automation
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Root folders
BASE_DIR = Path(__file__).parent
DIVISIONS_DIR = BASE_DIR / "divisions"


def fetch_prices(symbols: Dict[str, float]) -> Dict[str, float]:
    """Fetch latest close prices for provided tickers using yfinance.

    Args:
        symbols: Dictionary of ticker to share count.

    Returns:
        Dictionary of ticker to latest closing price.
    """

    # Early exit if there are no symbols
    tickers = list(symbols.keys())
    if not tickers:
        return {}

    # Download price data; use try/except to keep other divisions running
    prices: Dict[str, float] = {}
    try:
        data = yf.download(tickers=tickers, period="2d", progress=False, auto_adjust=False)
        # Handle multi-index columns when multiple tickers are requested
        if len(tickers) == 1:
            close_series = data["Close"]
        else:
            close_series = data["Close"].iloc[-1]

        # Extract latest close for each ticker
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    price = float(close_series.iloc[-1])
                else:
                    price = float(close_series[ticker])
                prices[ticker] = price
            except Exception as exc:  # noqa: BLE001 - explicit beginner handling
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


def update_division(division_path: Path) -> None:
    """Process a single division safely."""

    logging.info("Updating division: %s", division_path.name)

    try:
        # Define important file paths
        portfolio_path = division_path / "portfolio.csv"
        leaderboard_path = division_path / "leaderboard.csv"
        rules_path = division_path / "rules.json"

        # Ensure leaderboard exists with correct columns
        init_leaderboard(leaderboard_path)

        # Load division rules
        rules = load_rules(rules_path)

        # Load current portfolio
        portfolio = load_portfolio(portfolio_path)
        cash = float(portfolio.get("cash", 0.0))
        positions: Dict[str, float] = portfolio.get("positions", {})  # type: ignore[assignment]

        # Collect recent leaderboard context for strategies
        leaderboard_df = pd.read_csv(leaderboard_path) if leaderboard_path.exists() else pd.DataFrame()
        leaderboard_rows = leaderboard_df.tail(3).to_dict(orient="records") if not leaderboard_df.empty else []

        # Execute trading strategy before price calculations
        portfolio = run_strategy(portfolio, rules, leaderboard_rows)
        cash = float(portfolio.get("cash", 0.0))
        positions = portfolio.get("positions", {})  # type: ignore[assignment]
        save_portfolio(portfolio_path, portfolio)

        # Fetch latest prices for held tickers
        prices = fetch_prices(positions)

        # Compute total value
        total_value, _ = calculate_portfolio_value(cash, positions, prices)

        # Prepare leaderboard row
        today = dt.date.today().isoformat()
        row = {
            "date": today,
            "portfolio_value": round(total_value, 2),
            "cash": round(cash, 2),
            "positions_json": json.dumps(positions),
        }

        # Append to leaderboard
        append_leaderboard_row(leaderboard_path, row)

        # Save portfolio back (keeps format consistent)
        save_portfolio(portfolio_path, portfolio)

        logging.info("Finished division %s", division_path.name)
    except Exception as exc:  # noqa: BLE001
        # Log the error but do not crash the updater for other divisions
        logging.error("Division %s failed: %s", division_path.name, exc)


def main() -> None:
    """Load all divisions and update their leaderboards."""

    logging.info("Starting Beta Buster update")

    # Find all division folders
    divisions = list_divisions(DIVISIONS_DIR)
    if not divisions:
        logging.warning("No divisions found under %s", DIVISIONS_DIR)
        return

    # Update each division independently
    for division in divisions:
        update_division(division)

    logging.info("All divisions processed")


if __name__ == "__main__":
    main()
