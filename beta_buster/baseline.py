"""Baseline benchmark handling for Beta Buster divisions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yfinance as yf

from utils import load_json, save_json

BaselineData = Dict[str, float]


@dataclass
class BaselineState:
    """Typed baseline container for clarity."""

    units: float = 0.0
    initial_price: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "BaselineState":
        return cls(units=float(data.get("units", 0.0)), initial_price=float(data.get("initial_price", 0.0)))

    def to_dict(self) -> Dict[str, float]:
        return {"units": float(self.units), "initial_price": float(self.initial_price)}


def fetch_latest_price(ticker: str) -> Optional[float]:
    """Fetch the most recent close price for a ticker using yfinance."""

    if not ticker:
        return None
    try:
        data = yf.download(tickers=[ticker], period="2d", progress=False, auto_adjust=False)
        close_series = data["Close"]
        return float(close_series.iloc[-1])
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to fetch price for %s: %s", ticker, exc)
        return None


def ensure_baseline(path: Path, benchmark_ticker: str, starting_cash: float) -> BaselineState:
    """Load or initialize baseline exposure based on the benchmark."""

    existing = load_json(path)
    if existing and "units" in existing:
        return BaselineState.from_dict(existing)  # type: ignore[arg-type]

    price = fetch_latest_price(benchmark_ticker) or 0.0
    units = (float(starting_cash) / price) if price else 0.0
    baseline_state = BaselineState(units=units, initial_price=price)
    save_json(path, baseline_state.to_dict())
    return baseline_state


def compute_baseline_value(baseline: BaselineState, current_price: float) -> float:
    """Calculate the current value of the scaled benchmark."""

    return float(baseline.units) * float(current_price)

