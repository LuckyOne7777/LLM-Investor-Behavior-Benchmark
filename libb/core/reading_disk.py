from pathlib import Path
import pandas as pd
from libb.other.types_file import ModelSnapshot
import json

class DiskReader:
    def __init__(
        self,
        *,
        cash_path: Path,
        portfolio_path: Path,
        portfolio_history_path: Path,
        trade_log_path: Path,
        position_history_path: Path,
        pending_trades_path: Path,
        performance_path: Path,
        behavior_path: Path,
        sentiment_path: Path,
    ):
        self._cash_path = cash_path
        self._portfolio_path = portfolio_path
        self._portfolio_history_path = portfolio_history_path
        self._trade_log_path = trade_log_path
        self._position_history_path = position_history_path
        self._pending_trades_path = pending_trades_path
        self._performance_path = performance_path
        self._behavior_path = behavior_path
        self._sentiment_path = sentiment_path

    # ----------------------------------
    # File Helpers
    # ----------------------------------

    def _load_csv(self, path: Path) -> pd.DataFrame:
        """Helper for loading CSV at a given path. Return empty DataFrame for invalid paths."""
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()

    def _load_json(self, path: Path) -> list[dict]:
        """Helper for loading JSON files at a given path. Return empty list for invalid paths."""
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return []

    def _load_orders_dict(self, path: Path) -> dict[str, list[dict]]:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {"orders": []}

    def _load_cash(self) -> float:
        with open(self._cash_path, "r") as f:
            data = json.load(f)

        if "cash" not in data:
            raise RuntimeError(
                f"`cash.json` missing required key 'cash' at {self._cash_path}"
            )

        cash = data["cash"]

        try:
            return float(cash)
        except (TypeError, ValueError):
            raise RuntimeError(
                f"Invalid cash value in {self._cash_path}: {cash!r}"
            )

    # ----------------------------------
    # Snapshot Behavior
    # ----------------------------------

    def _save_disk_snapshot(self) -> ModelSnapshot:
        """
        Capture a snapshot of the last committed on-disk model state.

        This snapshot reflects persisted state only and is used for rollback
        after processing failures. In-memory runtime mutations that have not
        been flushed to disk are intentionally excluded.
        """
        return ModelSnapshot(
            cash=self._load_cash(),

            portfolio=self._load_csv(self._portfolio_path),
            portfolio_history=self._load_csv(self._portfolio_history_path),
            trade_log=self._load_csv(self._trade_log_path),
            position_history=self._load_csv(self._position_history_path),
            pending_trades=self._load_orders_dict(self._pending_trades_path),

            performance=self._load_json(self._performance_path),
            behavior=self._load_json(self._behavior_path),
            sentiment=self._load_json(self._sentiment_path),
        )
