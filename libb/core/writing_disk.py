from pathlib import Path
import json
from datetime import date
from libb.other.types_file import Log, ModelSnapshot, DiskLayout
from dataclasses import asdict
import pandas as pd

class DiskWriter:
    def __init__(self, *, layout: DiskLayout, run_date: date):
        self.layout = layout
        self.run_date = run_date



    # ----------------------------
    # Research & Reports
    # ----------------------------

    def save_deep_research(self, text: str) -> Path:
        path = self.layout.deep_research_dir / f"deep_research - {self.run_date}.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def save_daily_update(self, text: str) -> Path:
        path = self.layout.daily_reports_dir / f"daily_update - {self.run_date}.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def save_additional_log(
        self,
        file_name: str,
        text: str,
        folder: str = "additional_logs",
        append: bool = False,
    ) -> None:
        path = self.layout.research_dir / folder / file_name
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(text)

    # ----------------------------
    # Orders
    # ----------------------------

    def save_orders(self, orders: dict) -> None:
        with open(self.layout.pending_trades_path, "w") as f:
            json.dump(orders, f, indent=2)

    # ----------------------------
    # Metrics
    # ----------------------------

    def save_performance(self, performance_dict: dict) -> None:
        with open(self.layout.performance_path, "w") as f:
            json.dump(performance_dict, f, indent=2)

    # ----------------------------
    # Logging
    # ----------------------------
    
    def _save_logging_file_to_disk(self, log: Log):
        log_file_name = Path(f"{self.run_date}.json")
        full_path = self.layout.logging_dir / log_file_name
        with open(full_path, "w") as file:
            try:
                json.dump(asdict(log), file, indent=2)
            except Exception as e:
                    raise RuntimeError(f"Error while saving JSON log to {full_path}.") from e
        return
    
    # ----------------------------
    # Portfolio Artifact Saving
    # ----------------------------
    
    def _save_cash(self, cash: float) -> None:
        with open(self.layout.cash_path, "w") as f:
                json.dump({"cash": cash}, f, indent=2)


    def _override_json_file(self, data: list[dict] | dict[str, list[dict]], path: Path) -> None:
        with open(path, "w") as file:
            json.dump(data, file, indent=2)
        return
    
    def _override_csv_file(self, df: pd.DataFrame, path: Path) -> None:
        df.to_csv(path, mode="w", header=True, index=False)
        return

    # ----------------------------
    # Snapshot
    # ----------------------------

    def _load_snapshot_to_disk(self, snapshot: ModelSnapshot) -> None:
        """Override CSV and JSON disk artifacts based on prior disk snapshot."""
        
        self._override_csv_file(snapshot.portfolio, self.layout.portfolio_path)
        self._override_csv_file(snapshot.portfolio_history, self.layout.portfolio_history_path)
        self._override_csv_file(snapshot.trade_log, self.layout.trade_log_path)
        self._override_csv_file(snapshot.position_history, self.layout.position_history_path)

        self._override_json_file(snapshot.performance, self.layout.performance_path)
        self._override_json_file(snapshot.sentiment, self.layout.sentiment_path)
        self._override_json_file(snapshot.pending_trades, self.layout.pending_trades_path)
        self._override_json_file(snapshot.behavior, self.layout.behavior_path)
        return