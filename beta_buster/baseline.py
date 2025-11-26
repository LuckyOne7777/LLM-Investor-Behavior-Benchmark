"""Baseline benchmark handling for Beta Buster divisions."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

import yfinance as yf

Baseline = Dict[str, float]


def load_baseline(path: Path) -> Baseline:
    """Load a baseline JSON file from disk."""

    if not path.exists():
        raise FileNotFoundError(f"Baseline file missing: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_baseline(path: Path, data: Baseline) -> None:
    """Persist baseline data to disk."""

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _fetch_latest_price(ticker: str) -> float:
    """Fetch the latest close price for a ticker using yfinance."""

    data = yf.download(tickers=[ticker], period="2d", progress=False, auto_adjust=False)
    close_series = data["Close"]
    return float(close_series.iloc[-1])


def initialize_baseline_if_missing(portfolio: Dict[str, object], rules: Dict[str, object], baseline_path: Path) -> Baseline:
    """Ensure a baseline.json exists and return its contents."""

    if baseline_path.exists():
        existing = load_baseline(baseline_path)
        if "units" in existing and "initial_price" in existing:
            return existing

    benchmark = str(rules.get("benchmark", "")).strip()
    if not benchmark:
        raise ValueError("Rules must specify a benchmark ticker to initialize baseline")

    try:
        price = _fetch_latest_price(benchmark)
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to initialize baseline for %s: %s", benchmark, exc)
        raise

    units = float(portfolio.get("cash", 0.0)) / price if price else 0.0
    baseline = {"units": units, "initial_price": price}
    save_baseline(baseline_path, baseline)
    return baseline


def compute_baseline_value(baseline: Baseline, current_price: float) -> float:
    """Calculate the current value of the scaled benchmark."""

    units = float(baseline.get("units", 0.0))
    return units * float(current_price)
