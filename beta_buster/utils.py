"""Utility helpers for Beta Buster.

This module keeps small helpers isolated to keep update_all.py focused and readable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List
import os
import pandas as pd

# Type aliases for clarity
Portfolio = Dict[str, object]
Positions = Dict[str, float]
    
def load_json(path: Path) -> Dict[str, object]:
    """Load JSON content from disk.

    Args:
        path: File path to read.

    Returns:
        Parsed JSON as a dictionary.
    """

    # Read the file content
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, object]) -> None:
    """Write JSON content to disk with indentation."""
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_portfolio(path: Path) -> Portfolio:
    """Load a portfolio CSV into a dictionary with types.

    The CSV is expected to contain columns: cash, positions_json.
    """

    if not path.exists():
        raise FileNotFoundError(f"Portfolio file missing: {path}")

    df = pd.read_csv(path)

    # Ensure required columns exist
    if "cash" not in df.columns or "positions_json" not in df.columns:
        raise ValueError(f"Portfolio CSV {path} missing required columns")

    # Convert the first row into our dictionary
    cash = float(df.loc[0, "cash"])
    positions_raw = df.loc[0, "positions_json"]
    positions: Positions = json.loads(positions_raw) if isinstance(positions_raw, str) else {}

    return {"cash": cash, "positions": positions}


def save_portfolio(path: Path, portfolio: Portfolio) -> None:
    """Save a portfolio dictionary back to CSV."""

    df = pd.DataFrame(
        [
            {
                "cash": portfolio.get("cash", 0.0),
                "positions_json": json.dumps(portfolio.get("positions", {})),
            }
        ]
    )
    df.to_csv(path, index=False)


def init_leaderboard(path: Path) -> None:
    """Create or upgrade a leaderboard CSV to the current schema."""

    columns = ["date", "portfolio_value", "benchmark_value", "alpha", "cash", "positions_json"]

    if path.exists():
        df = pd.read_csv(path)
        missing = [col for col in columns if col not in df.columns]
        if missing:
            for col in missing:
                df[col] = None
            df = df[columns]
            df.to_csv(path, index=False)
        return

    df = pd.DataFrame(columns=columns)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def append_leaderboard_row(path: Path, row: Dict[str, object]) -> None:
    """Append a single row to the leaderboard CSV."""

    columns = ["date", "portfolio_value", "benchmark_value", "alpha", "cash", "positions_json"]
    df = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=columns)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df = df[columns]
    df.to_csv(path, index=False)


def list_divisions(root: Path) -> List[Path]:
    """Return all division directories contained in the root divisions folder."""

    if not root.exists():
        return []

    return [p for p in root.iterdir() if p.is_dir()]
