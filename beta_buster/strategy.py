"""Trading strategy logic for Beta Buster divisions.

This module is designed for extensibility: new model types can be added without
changing callers. The dispatcher in ``run_strategy`` routes to specific strategy
implementations based on ``rules['model_type']``.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import yfinance as yf
from openai import OpenAI

from utils import load_json

Portfolio = Dict[str, object]
Positions = Dict[str, float]
Rules = Dict[str, object]


# ---------------------------------------------------------------------------
# Rules loading
# ---------------------------------------------------------------------------

def load_rules(path: Path) -> Rules:
    """Load division rules from disk."""

    if not path.exists():
        raise FileNotFoundError(f"Rules file missing: {path}")
    return load_json(path)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def validate_trade(action: str, ticker: Optional[str], shares: Optional[float]) -> bool:
    """Validate the basic shape of a trade decision."""

    valid_actions = {"buy", "sell", "hold"}
    if action not in valid_actions:
        logging.warning("Invalid action '%s' from strategy", action)
        return False
    if action == "hold":
        return True

    if not ticker or not isinstance(ticker, str):
        logging.warning("Missing or invalid ticker for trade")
        return False
    if shares is None:
        logging.warning("Missing share count for trade")
        return False
    try:
        if float(shares) <= 0:
            logging.warning("Share count must be positive: %s", shares)
            return False
    except (TypeError, ValueError):
        logging.warning("Share count is not a number: %s", shares)
        return False
    return True


def _fetch_single_price(ticker: str) -> Optional[float]:
    """Fetch the most recent close price for a single ticker."""

    try:
        data = yf.download(tickers=[ticker], period="2d", progress=False, auto_adjust=False)
        close_series = data["Close"]
        price = float(close_series.iloc[-1])
        return price
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to fetch price for %s: %s", ticker, exc)
        return None


def _apply_trade(portfolio: Portfolio, trade: Dict[str, object]) -> Portfolio:
    """Apply a trade decision to the portfolio with basic validation."""

    action = str(trade.get("action", "")).lower()
    ticker = trade.get("ticker")
    shares = trade.get("shares")

    if not validate_trade(action, ticker, shares):
        logging.info("Trade validation failed; keeping portfolio unchanged")
        return run_baseline_strategy(portfolio)

    updated = {
        "cash": float(portfolio.get("cash", 0.0)),
        "positions": dict(portfolio.get("positions", {})),
    }
    positions: Positions = updated["positions"]  # type: ignore[assignment]

    if action == "hold":
        return updated

    ticker_str = str(ticker).upper()
    share_count = float(shares)
    price = _fetch_single_price(ticker_str)
    if price is None:
        logging.warning("Skipping trade because price was unavailable")
        return updated

    if action == "buy":
        cost = price * share_count
        if cost > updated["cash"]:
            logging.warning("Insufficient cash to buy %s shares of %s", share_count, ticker_str)
            return updated
        updated["cash"] -= cost
        positions[ticker_str] = positions.get(ticker_str, 0.0) + share_count
    elif action == "sell":
        current_shares = positions.get(ticker_str, 0.0)
        if share_count > current_shares:
            logging.warning("Not enough shares to sell %s of %s", share_count, ticker_str)
            return updated
        proceeds = price * share_count
        updated["cash"] += proceeds
        remaining = current_shares - share_count
        if remaining > 0:
            positions[ticker_str] = remaining
        else:
            positions.pop(ticker_str, None)

    return updated


# ---------------------------------------------------------------------------
# Strategy implementations
# ---------------------------------------------------------------------------

def run_baseline_strategy(portfolio: Portfolio, rules: Optional[Rules] = None, leaderboard_rows: Optional[List[Dict[str, object]]] = None) -> Portfolio:  # noqa: D417 - optional args unused for parity
    """Return the portfolio unchanged as a trivial baseline."""

    return {
        "cash": float(portfolio.get("cash", 0.0)),
        "positions": dict(portfolio.get("positions", {})),
    }


def run_llm_strategy(portfolio: Portfolio, rules: Rules, leaderboard_rows: Optional[List[Dict[str, object]]] = None) -> Portfolio:
    """Call an OpenAI model to decide on a trade and update the portfolio."""

    model_name = str(rules.get("model_name", "")).strip()
    if not model_name:
        logging.warning("No model_name specified in rules; falling back to baseline strategy")
        return run_baseline_strategy(portfolio)

    leaderboard_rows = leaderboard_rows or []
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = {
        "role": "user",
        "content": (
            "You are a trading assistant. Review the provided portfolio, rules, and recent leaderboard performance. "
            "Decide whether to buy, sell, or hold a single ticker today. "
            "ONLY respond with JSON containing action, ticker, shares.\n"
            f"Portfolio JSON: {json.dumps(portfolio)}\n"
            f"Rules JSON: {json.dumps(rules)}\n"
            f"Last 3 leaderboard rows: {json.dumps(leaderboard_rows)}\n"
            "Buy, sell, or hold? Respond in pure JSON with keys action, ticker, shares."
        ),
    }

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise trading bot. Output only valid JSON with keys action, ticker, shares.",
                },
                prompt,
            ],
            temperature=0.0,
        )
    except Exception as exc:  # noqa: BLE001
        logging.error("OpenAI request failed: %s", exc)
        return run_baseline_strategy(portfolio)

    content = response.choices[0].message.content if response.choices else None
    if not content:
        logging.warning("No content returned from model; using baseline strategy")
        return run_baseline_strategy(portfolio)

    try:
        trade_decision = json.loads(content)
    except json.JSONDecodeError:
        logging.warning("Model response was not valid JSON: %s", content)
        return run_baseline_strategy(portfolio)

    # Validate expected keys explicitly
    if not isinstance(trade_decision, dict) or not {"action", "ticker", "shares"}.issubset(trade_decision.keys()):
        logging.warning("Model response missing required keys: %s", trade_decision)
        return run_baseline_strategy(portfolio)

    return _apply_trade(portfolio, trade_decision)


def run_rule_based_strategy(portfolio: Portfolio, rules: Rules, leaderboard_rows: Optional[List[Dict[str, object]]] = None) -> Portfolio:  # noqa: D417 - leaderboard_rows reserved for future use
    """Placeholder for future rule-based strategies.

    Currently mirrors the baseline behaviour. Implement custom logic here when a
    rule-based engine is introduced.
    """

    logging.info("Rule-based strategy not implemented; defaulting to baseline")
    return run_baseline_strategy(portfolio)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def run_strategy(portfolio: Portfolio, rules: Rules, leaderboard_rows: Optional[List[Dict[str, object]]] = None) -> Portfolio:
    """Dispatch to the correct strategy implementation.

    Supported types today:
        - baseline
        - llm
        - rule_based (placeholder)
    """

    strategy_type = rules.get("model_type", "baseline")
    strategy_type = str(strategy_type).lower()

    if strategy_type == "baseline":
        return run_baseline_strategy(portfolio, rules, leaderboard_rows)
    elif strategy_type == "llm":
        return run_llm_strategy(portfolio, rules, leaderboard_rows)
    elif strategy_type == "rule_based":
        return run_rule_based_strategy(portfolio, rules, leaderboard_rows)

    logging.info("Unknown model_type '%s'; falling back to baseline", strategy_type)
    return run_baseline_strategy(portfolio, rules, leaderboard_rows)

