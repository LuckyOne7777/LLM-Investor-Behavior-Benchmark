from pathlib import Path
from datetime import date, datetime, UTC, time
from zoneinfo import ZoneInfo
from shutil import rmtree
import json

import pandas as pd

from libb.other.types_file import ModelSnapshot, Log
from libb.execution.utils import is_nyse_open
from libb.metrics.sentiment_metrics import analyze_sentiment
from libb.user_data.news import  _get_portfolio_news
from libb.user_data.logs import _recent_execution_logs

from libb.core.processing import Processing
from libb.core.writing_disk import DiskWriter

class LIBBmodel:

    """
    Stateful trading model that manages portfolio data, metrics, research,
    and daily execution for a single run date.
    """
    def __init__(self, model_path: Path | str, starting_cash: float = 10_000, 
                 run_date: str | date | None = None):
        """
        Initialize the trading model and load persisted state.

        Args:
            model_path: Root directory where all model data is stored.
            starting_cash: Initial cash balance if no portfolio exists.
            date: Run date for the model. If None, defaults to today.
        """
        if run_date is None:
            run_date = pd.Timestamp.now().date()
        else:
            run_date = pd.Timestamp(run_date).date()

        self.start_time= datetime.now(UTC)

        self.STARTING_CASH: float = starting_cash
        self._root: Path = Path(model_path)
        self._model_path: str = str(model_path)
        self.run_date: date = run_date

        # directories
        self._portfolio_dir: Path = self._root / "portfolio"
        self._metrics_dir: Path = self._root / "metrics"
        self._research_dir: Path = self._root / "research"
        self._logging_dir: Path = self._root / "logging"

        self._deep_research_file_folder_path: Path = self._research_dir / "deep_research"
        self._daily_reports_file_folder_path: Path = self._research_dir / "daily_reports"

        # paths in portfolio
        self._portfolio_history_path: Path = self._portfolio_dir / "portfolio_history.csv"
        self._pending_trades_path: Path = self._portfolio_dir / "pending_trades.json"
        self._cash_path: Path = self._portfolio_dir / "cash.json"
        self._portfolio_path: Path = self._portfolio_dir / "portfolio.csv"
        self._trade_log_path: Path = self._portfolio_dir / "trade_log.csv"
        self._position_history_path: Path = self._portfolio_dir / "position_history.csv"

        # paths in metrics
        self._behavior_path: Path = self._metrics_dir / "behavior.json"
        self._performance_path: Path = self._metrics_dir / "performance.json"
        self._sentiment_path: Path = self._metrics_dir / "sentiment.json"

        self.ensure_file_system()
        self._hydrate_from_disk()

        self.writer = DiskWriter(

            research_dir=self._research_dir,
            deep_research_dir=self._deep_research_file_folder_path,
            daily_reports_dir=self._daily_reports_file_folder_path,
            pending_trades_path=self._pending_trades_path,
            logging_dir=self._logging_dir,
            _cash_path=self._cash_path,
            run_date=self.run_date,
            _logging_dir=self._logging_dir,

            portfolio_path=self._portfolio_path,
            portfolio_history_path=self._portfolio_history_path,
            trade_log_path=self._trade_log_path,
            position_history_path=self._position_history_path,
            performance_path=self._performance_path,
            sentiment_path=self._sentiment_path,
            behavior_path=self._behavior_path,
                )


        self.filled_orders: int = 0
        self.failed_orders: int = 0
        self.skipped_orders: int = 0

        self.STARTUP_DISK_SNAPSHOT: ModelSnapshot | None = self._save_disk_snapshot()
        self._instance_is_valid: bool = True

# ----------------------------------
# Filesystem & Persistence
# ----------------------------------

    def ensure_file_system(self):
        "Create and set up all files/folders needed for processing and metrics. Automatically called during construction."
        for dir in [self._root, self._portfolio_dir, self._metrics_dir, self._research_dir, self._daily_reports_file_folder_path, 
                    self._deep_research_file_folder_path, self._logging_dir]:
            self._ensure_dir(dir)

        # portfolio files
        self._ensure_file(self._portfolio_history_path, "date,equity,cash,positions_value,return_pct\n")
        self._ensure_file(self._pending_trades_path, '{"orders": []}')

        self._ensure_file(self._cash_path, json.dumps({"cash": self.STARTING_CASH}) )

        self._ensure_file(self._portfolio_path, "ticker,shares,buy_price,cost_basis,stop_loss,market_price,market_value,unrealized_pnl\n")
        self._ensure_file(self._trade_log_path, "date,ticker,action,shares,price,cost_basis,PnL,rationale,confidence,status,reason\n")
        self._ensure_file(self._position_history_path, "date,ticker,shares,avg_cost,stop_loss,market_price,market_value,unrealized_pnl\n")

        # metrics files
        self._ensure_file(self._behavior_path, "[]")
        self._ensure_file(self._performance_path, "[]")
        self._ensure_file(self._sentiment_path, "[]")
        return
    
    def _hydrate_from_disk(self) -> None:
        "Match objects in memory from disk state."
        self.portfolio: pd.DataFrame = self._load_csv(self._portfolio_path)
        self.cash: float = self._load_cash()
        self.portfolio_history: pd.DataFrame = self._load_csv(self._portfolio_history_path)
        self.trade_log: pd.DataFrame = self._load_csv(self._trade_log_path)
        self.position_history: pd.DataFrame = self._load_csv(self._position_history_path)

        self.pending_trades: dict[str, list[dict]] = self._load_orders_dict(self._pending_trades_path)
        self.performance: list[dict] = self._load_json(self._performance_path)
        self.behavior: list[dict] = self._load_json(self._behavior_path)
        self.sentiment: list[dict] = self._load_json(self._sentiment_path)


    def _reset_runtime_state(self) -> None:
        self.filled_orders = 0
        self.failed_orders = 0
        self.skipped_orders = 0
        self.start_time = datetime.now(UTC)
        self.STARTUP_DISK_SNAPSHOT = None

    
    def reset_run(self, cli_check: bool = True, auto_ensure: bool = False) -> None:
         
        """
        Reset model state by deleting all on-disk artifacts under the model root.

        By default, this method ONLY deletes filesystem state. The current
        LIBBmodel instance remains alive, and in-memory runtime state is NOT
        reset unless `auto_ensure=True` is provided.

        When `auto_ensure=True`, this method performs a full logical reset:
            - Deletes all on-disk model artifacts
            - Recreates required filesystem structure
            - Rehydrates disk-backed state into memory
            - Resets all runtime-only state (counters, timestamps, snapshots)
            - Establishes a new startup disk snapshot

        With `auto_ensure=True`, the resulting model state is equivalent to a
        freshly constructed LIBBmodel instance pointing at the same path,
        without restarting the Python process.

        Args:
            cli_check (bool): Require interactive confirmation before deleting
                all model files. Defaults to True.

            auto_ensure (bool): Perform a full disk + runtime reset after
                deletion. Defaults to False.
        """
        root = self._root.resolve()

        self._instance_is_valid = False

        if cli_check:
            user_decision = None
            while user_decision not in {"y", "n"}:
                user_decision = input(f"Warning: reset_run() is about to delete all contents within {root}. Proceed? (y/n) ")
            if user_decision == "n":
                raise RuntimeError("Please remove reset_run call from your workflow.")

        # Block filesystem root (/, C:\, D:\, UNC share roots, etc.)
        if root == Path(root.anchor):
            raise RuntimeError(f"Refusing to delete filesystem root: {root}")

        for child in root.iterdir():
            if child.is_dir():
                rmtree(child)
            else:
                child.unlink()
        if auto_ensure:
            self.ensure_file_system()
            self._hydrate_from_disk()
            self._reset_runtime_state()
            self.STARTUP_DISK_SNAPSHOT = self._save_disk_snapshot()
            self._instance_is_valid = True
        return

    def _ensure_dir(self, path: Path) -> None:
        """Helper for creating folders."""
        path.mkdir(parents=True, exist_ok=True)
        return

    def _ensure_file(self, path: Path, default_content: str = "") -> None:
        """Helper for creating files and writing default content."""
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(default_content, encoding="utf-8")

# ----------------------------------
# File Helpers
# ----------------------------------


    def _load_csv(self, path: Path) -> pd.DataFrame:
        """Helper for loading CSV at a given path. Return empty DataFrame for invalid paths."""
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()

    def _load_json(self, path: Path) -> list[dict]:
        "Helper for loading JSON files at a given path. Return empty list for invalid paths."
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
        cash= self._load_cash(),

        portfolio= self._load_csv(self._portfolio_path),
        portfolio_history= self._load_csv(self._portfolio_history_path),
        trade_log= self._load_csv(self._trade_log_path),
        position_history=self._load_csv(self._position_history_path),
        pending_trades= self._load_orders_dict(self._pending_trades_path),

        performance= self._load_json(self._performance_path),
        behavior= self._load_json(self._behavior_path),
        sentiment= self._load_json(self._sentiment_path),
        )
    

# ----------------------------------
# Portfolio Processing
# ----------------------------------


    def process_portfolio(self) -> None:
        "Wrapper for all portfolio processing."
        ""
        today = pd.Timestamp.now().date()


        if self.run_date > today:
            raise RuntimeError(
            f"""Cannot process portfolio: run_date ({self.run_date}) is ahead
            of the current date ({today})."""
            )
        if not self._instance_is_valid:
                raise RuntimeError("LIBBmodel instance is invalid after failure; create a new instance to avoid divergence from state.")

        if is_nyse_open(self.run_date):
            try:
                processing = Processing(run_date=self.run_date, portfolio=self.portfolio, cash=self.cash,
                                _trade_log_path=self._trade_log_path, portfolio_history=self.portfolio_history, 
                                _position_history_path=self._position_history_path,
                                  _portfolio_history_path=self._portfolio_history_path,
                                _portfolio_path=self._portfolio_path, _model_path=self._model_path)

                self.pending_trades, self.cash = processing.processing(self.pending_trades)
                self.filled_orders, self.failed_orders, self.skipped_orders = processing.get_order_status_count()
                self._save_cash(self.cash)
                self.save_orders(self.pending_trades)
                self._save_new_logging_file()
            except Exception as e:
                self._instance_is_valid = False
                if self.STARTUP_DISK_SNAPSHOT is None:
                    raise RuntimeError("No startup disk snapshot available for rollback; disk may be corrupted.")
                else:
                    self.writer._load_snapshot_to_disk(self.STARTUP_DISK_SNAPSHOT)
                self._save_new_logging_file()
                raise SystemError("Processing failed: disk state has been reset to snapshot created on startup.") from e
            else:
                self._save_new_logging_file()

# ----------------------------------
# Disk Writing
# ----------------------------------


    def save_deep_research(self, txt: str) -> Path:
        return self.writer.save_deep_research(txt)
    
    def save_daily_update(self, txt: str) -> Path:
        return self.writer.save_daily_update(txt)
    
    def save_orders(self, json_block: dict) -> None:
        self.writer.save_orders(json_block)

    def save_additional_log(self, file_name: str, text: str, folder: str="additional_logs", append: bool=False) -> None:
        self.writer.save_additional_log(file_name, text, folder, append)
    

    def _save_cash(self, cash: float) -> None:
        self.writer._save_cash(cash)
    

# ----------------------------------
# Logging
# ----------------------------------

    def _create_log_dict(self, status: str, error: Exception | str) -> Log:

        portfolio_equity = self.portfolio["market_value"].sum() + self.cash

        nyse_open_on_date = is_nyse_open(self.run_date)

        NY_TZ = ZoneInfo("America/New_York")
        MARKET_CLOSE = time(16, 0) # 4PM

        is_today = self.run_date == pd.Timestamp.now().date()

        if is_today:
            start_time_ny = self.start_time.astimezone(NY_TZ)
            created_after_close = start_time_ny.time() >= MARKET_CLOSE
        else:
            created_after_close = True

        eligible_for_execution = nyse_open_on_date and created_after_close

        weekday_name = str(self.run_date.strftime("%A"))

        end_time = datetime.now(UTC)
        
        log = Log(
            date=str(self.run_date),
            weekday=weekday_name,
            started_at=str(self.start_time),
            finished_at=str(end_time),
            nyse_open_on_date=nyse_open_on_date,
            created_after_close=created_after_close,
            eligible_for_execution=eligible_for_execution,
            processing_status=status,
            orders_processed=self.filled_orders,
            orders_failed=self.failed_orders,
            orders_skipped=self.skipped_orders,
            portfolio_value=portfolio_equity,
            error=error,
                )


        return log 
    
    def _save_new_logging_file(self, status: str = "SUCCESS", error: Exception | str = "none"):
        log = self._create_log_dict(status, error)
        self.writer._save_logging_file_to_disk(log)
# ----------------------------------
# Calculate Metrics
# ----------------------------------

    
    def analyze_sentiment(self, text: str, report_type: str="Unknown") -> dict:
        """
        Analyze sentiment for the given text and persist the result.

        The sentiment log is appended to the in-memory sentiment list
        and written to disk as JSON.

        Args:
            text (`str`, required): Text to analyze.
            report_type (`str`, optional): Type or source of the report.
                Defaults to "Unknown".

        Returns:
            dict: Sentiment analysis log for the given text.
        """
        log = analyze_sentiment(text, self.run_date, report_type=report_type)
        self.sentiment.append(log)
        with open(self._sentiment_path, "w") as file:
            json.dump(self.sentiment, file, indent=2)
        return log

# ----------------------------------
# News
# ----------------------------------

    def get_portfolio_news(self, n: int = 2, summary_limit: int = 150):
        """Return current-day portfolio news (see services.news.get_portfolio_news)."""
        return _get_portfolio_news(self.portfolio, n=n, summary_limit=summary_limit)
    

# ----------------------------------
# user logs
# ----------------------------------
    def recent_execution_logs(self, date: None | str | datetime = None, look_back: int = 5) -> pd.DataFrame:
        """
        Return recent execution logs for the model (see `libb.user_data.logs._recent_execution_logs`).
        """
        if date is None:
            effective_date = self.run_date
        else:
            effective_date = pd.Timestamp(date).date()
        return _recent_execution_logs(self._trade_log_path, date=effective_date, look_back=look_back)
    
    
    