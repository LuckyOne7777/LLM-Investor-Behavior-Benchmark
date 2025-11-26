"""Utility helpers for Beta Buster.

This module centralizes small helpers used across the project. Functions focus on
robustness and automatic file creation so GitHub Actions runs never fail due to
missing artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

# Type aliases for clarity
Portfolio = Dict[str, object]
Positions = Dict[str, float]


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> Dict[str, object]:
    """Load JSON content from disk.

    Args:
        path: File path to read.

    Returns:
        Parsed JSON as a dictionary. Returns an empty dict if the file is
        missing to keep callers resilient.
    """

    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, object]) -> None:
    """Write JSON content to disk with indentation."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Portfolio helpers
# ---------------------------------------------------------------------------

def ensure_portfolio_csv(path: Path, default_cash: float = 10000.0) -> None:
    """Ensure a portfolio CSV exists with the expected schema.

    Schema:
        cash,positions_json
        10000,{}
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["cash", "positions_json"]

    if not path.exists():
        df = pd.DataFrame([[default_cash, json.dumps({})]], columns=columns)
        df.to_csv(path, index=False)
        return

    # Upgrade existing files if columns are missing
    df = pd.read_csv(path)
    missing = [col for col in columns if col not in df.columns]
    for col in missing:
        df[col] = default_cash if col == "cash" else json.dumps({})
    df = df[columns]
    df.to_csv(path, index=False)


def load_portfolio(path: Path) -> Portfolio:
    """Load a portfolio CSV into a dictionary with types."""

    ensure_portfolio_csv(path)
    df = pd.read_csv(path)

    cash = float(df.loc[0, "cash"]) if not df.empty else 0.0
    positions_raw = df.loc[0, "positions_json"] if not df.empty else "{}"
    positions: Positions = json.loads(positions_raw) if isinstance(positions_raw, str) else {}
    return {"cash": cash, "positions": positions}


def save_portfolio(path: Path, portfolio: Portfolio) -> None:
    """Save a portfolio dictionary back to CSV."""

    ensure_portfolio_csv(path)
    df = pd.DataFrame(
        [
            {
                "cash": float(portfolio.get("cash", 0.0)),
                "positions_json": json.dumps(portfolio.get("positions", {})),
            }
        ]
    )
    df.to_csv(path, index=False)


# ---------------------------------------------------------------------------
# Leaderboard helpers
# ---------------------------------------------------------------------------

def ensure_leaderboard_csv(path: Path) -> None:
    """Ensure a leaderboard CSV exists with required columns.

    If the file exists but is missing any columns, they are added while
    preserving existing data.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["date", "portfolio_value", "benchmark_value", "alpha", "cash", "positions_json"]

    if not path.exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False)
        return

    df = pd.read_csv(path)
    missing = [col for col in columns if col not in df.columns]
    for col in missing:
        df[col] = None
    df = df[columns]
    df.to_csv(path, index=False)


def list_divisions(root: Path) -> List[Path]:
    """Return all division directories contained in the root divisions folder."""

    if not root.exists():
        return []
    return [p for p in root.iterdir() if p.is_dir()]

