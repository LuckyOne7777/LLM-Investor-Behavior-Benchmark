from pathlib import Path
import json
from datetime import date
from libb.other.types_file import Log
import pandas as pd

class DiskWriter:
    def __init__(
        self,
        *,
        research_dir: Path,
        deep_research_dir: Path,
        daily_reports_dir: Path,
        pending_trades_path: Path,
        run_date: date,
        logging_dir: Path,
        _cash_path: Path,
        _logging_dir: Path):

        self._logging_dir = _logging_dir
        self.research_dir = research_dir
        self.deep_research_dir = deep_research_dir
        self.daily_reports_dir = daily_reports_dir
        self.pending_trades_path = pending_trades_path
        self.run_date = run_date
        self.logging_dir = logging_dir
        self._cash_path = _cash_path

    # ----------------------------
    # Research & Reports
    # ----------------------------

    def save_deep_research(self, text: str) -> Path:
        path = self.deep_research_dir / f"deep_research - {self.run_date}.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def save_daily_update(self, text: str) -> Path:
        path = self.daily_reports_dir / f"daily_update - {self.run_date}.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def save_additional_log(
        self,
        file_name: str,
        text: str,
        folder: str = "additional_logs",
        append: bool = False,
    ) -> None:
        path = self.research_dir / folder / file_name
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(text)

    # ----------------------------
    # Orders
    # ----------------------------

    def save_orders(self, orders: dict) -> None:
        with open(self.pending_trades_path, "w") as f:
            json.dump(orders, f, indent=2)

    # ----------------------------
    # Logging
    # ----------------------------
    
    def _save_logging_file_to_disk(self, log: Log):
        log_file_name = Path(f"{self.run_date}.json")
        full_path = self._logging_dir / log_file_name
        with open(full_path, "w") as file:
            try:
                json.dump(log, file, indent=2)
            except Exception as e:
                    raise RuntimeError(f"Error while saving JSON log to {full_path}.") from e
        return
    
    # ----------------------------
    # Portfolio Artifact Saving
    # ----------------------------
    
    def _save_cash(self, cash: float) -> None:
        with open(self._cash_path, "w") as f:
                json.dump({"cash": cash}, f, indent=2)


    def _override_json_file(self, data: list[dict] | dict[str, list[dict]], path: Path) -> None:
        with open(path, "w") as file:
            json.dump(data, file, indent=2)
        return
    
    def _override_csv_file(self, df: pd.DataFrame, path: Path) -> None:
        df.to_csv(path, mode="w", header=True, index=False)
        return
