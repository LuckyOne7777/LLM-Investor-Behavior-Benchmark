from pathlib import Path
import pandas as pd
from libb.other.types_file import ModelSnapshot, DiskLayout
import json

class DiskReader:
    def __init__(self, layout: DiskLayout):
        self.layout = layout


    # ----------------------------------
    # File Helpers
    # ----------------------------------

    def load_csv(self, path: Path) -> pd.DataFrame:
        """Helper for loading CSV at a given path. Return empty DataFrame for invalid paths."""
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()

    def load_json(self, path: Path) -> list[dict]:
        """Helper for loading JSON files at a given path. Return empty list for invalid paths."""
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return []

    def load_orders_dict(self, path: Path) -> dict[str, list[dict]]:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {"orders": []}

    def load_cash(self) -> float:
        with open(self.layout.cash_path, "r") as f:
            data = json.load(f)

        if "cash" not in data:
            raise RuntimeError(
                f"`cash.json` missing required key 'cash' at {self.layout.cash_path}"
            )

        cash = data["cash"]

        try:
            return float(cash)
        except (TypeError, ValueError):
            raise RuntimeError(
                f"Invalid cash value in {self.layout.cash_path}: {cash!r}"
            )

    # ----------------------------------
    # Snapshot Behavior
    # ----------------------------------

    def save_disk_snapshot(self) -> ModelSnapshot:
        """
        Capture a snapshot of the last committed on-disk model state.

        This snapshot reflects persisted state only and is used for rollback
        after processing failures. In-memory runtime mutations that have not
        been flushed to disk are intentionally excluded.
        """
        return ModelSnapshot(
            cash=self.load_cash(),

            portfolio=self.load_csv(self.layout.portfolio_path),
            portfolio_history=self.load_csv(self.layout.portfolio_history_path),
            trade_log=self.load_csv(self.layout.trade_log_path),
            position_history=self.load_csv(self.layout.position_history_path),
            pending_trades=self.load_orders_dict(self.layout.pending_trades_path),

            performance=self.load_json(self.layout.performance_path),
            behavior=self.load_json(self.layout.behavior_path),
            sentiment=self.load_json(self.layout.sentiment_path),
        )
