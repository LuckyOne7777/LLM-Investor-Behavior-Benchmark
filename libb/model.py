from pathlib import Path
from datetime import date, datetime, UTC, time
from zoneinfo import ZoneInfo
from shutil import rmtree
from typing import cast
import json

import pandas as pd

from libb.other.types_file import ModelSnapshot, Log, DiskLayout, MarketDataObject, MarketHistoryObject
from libb.other.config_setup import verifiy_config, set_config

from libb.execution.utils import is_nyse_open
from libb.execution.get_market_data import download_data_on_given_date, download_data_on_given_range

from libb.user_data.logs import _recent_execution_logs

from libb.graphs.sentiment import plot_equity_and_sentiment
from libb.graphs.equity import plot_equity_vs_baseline, plot_equity

from libb.metrics.performance_metrics import total_performance_calculations
from libb.metrics.behavior_metrics import total_behavioral_metrics
from libb.metrics.sentiment_metrics import analyze_sentiment


from libb.core.processing import Processing
from libb.core.writing_disk import DiskWriter
from libb.core.reading_disk import DiskReader

class LIBBmodel:

    """
    Stateful trading model that manages portfolio data, metrics, research,
    and daily execution for a single run date.
    """
    def __init__(self, model_path: Path | str, run_date: str | date | None = None, 
                 config: dict | None = None):
        """
        Initialize the trading model and load persisted state.

        Args:
            model_path: Root directory where all model data is stored.
            run_date: Run date for the model. If None, defaults to today.
            config: Optional configuration dictionary. If None, defaults are used.
                See docs/workflow.md for available keys and defaults.
        """
        if run_date is None:
            run_date = pd.Timestamp.now().date()
        else:
            run_date = pd.Timestamp(run_date).date()

        self.start_time = datetime.now(UTC)

        self.passed_verified_config: dict = verifiy_config(config)
        self._root: Path = Path(model_path)
        self._model_path: str = str(model_path)
        self.run_date: date = run_date

        self.layout: DiskLayout = DiskLayout.from_root(self._root)

        self.writer: DiskWriter = DiskWriter(layout=self.layout, run_date=self.run_date)

        self.reader: DiskReader = DiskReader(layout=self.layout)

        self.ensure_file_system()
        self._hydrate_from_disk()
        self._sync_config()

        self.filled_orders: int = 0
        self.failed_orders: int = 0
        self.skipped_orders: int = 0

        self.STARTUP_DISK_SNAPSHOT: ModelSnapshot | None = self.reader.save_disk_snapshot()
        self._instance_is_valid: bool = True

# ----------------------------------
# Filesystem & Persistence
# ----------------------------------

    def ensure_file_system(self):
        "Create and set up all files/folders needed for processing and metrics. Automatically called during construction."
        for dir in [self._root, self.layout.portfolio_dir, self.layout.metrics_dir, self.layout.research_dir, self.layout.daily_reports_dir, 
                    self.layout.deep_research_dir, self.layout.logging_dir]:
            self._ensure_dir(dir)

        # portfolio files
        self._ensure_file(self.layout.portfolio_history_path, "date,equity,cash,positions_value,daily_return_pct,overall_return_pct\n")
        self._ensure_file(self.layout.pending_trades_path, '{"orders": []}')

        self._ensure_file(self.layout.cash_path, json.dumps({"cash": self.passed_verified_config["starting_cash"]}) )

        self._ensure_file(self.layout.portfolio_path, "ticker,shares,buy_price,cost_basis,stop_loss,market_price,market_value,unrealized_pnl\n")
        self._ensure_file(self.layout.trade_log_path, "date,ticker,action,order_type,shares,limit_price,executed_price,stop_loss,cost_basis,PnL,rationale,confidence,status,reason\n")
        self._ensure_file(self.layout.position_history_path, "date,ticker,shares,avg_cost,stop_loss,market_price,market_value,unrealized_pnl\n")

        # metrics files
        self._ensure_file(self.layout.behavior_path, "[]")
        self._ensure_file(self.layout.performance_path, "[]")
        self._ensure_file(self.layout.sentiment_path, "[]")
        self._ensure_file(self.layout.config_path, json.dumps(self.passed_verified_config))
        return
    
    def _hydrate_from_disk(self) -> None:
        "Match objects in memory from disk state."
        self.portfolio: pd.DataFrame = self.reader.load_csv(self.layout.portfolio_path)
        self.cash: float = self.reader.load_cash()
        self.portfolio_history: pd.DataFrame = self.reader.load_csv(self.layout.portfolio_history_path)
        self.trade_log: pd.DataFrame = self.reader.load_csv(self.layout.trade_log_path)
        self.position_history: pd.DataFrame = self.reader.load_csv(self.layout.position_history_path)

        self.CONFIG: dict = cast(dict, self.reader.load_json(self.layout.config_path))
        set_config(self.CONFIG)
        self.STARTING_CASH = self.CONFIG["starting_cash"]

        self.pending_trades: dict[str, list[dict]] = self.reader.load_orders_dict(self.layout.pending_trades_path)
        self.performance: list[dict] = self.reader.load_json(self.layout.performance_path)
        self.behavior: list[dict] = self.reader.load_json(self.layout.behavior_path)
        self.sentiment: list[dict] = self.reader.load_json(self.layout.sentiment_path)


    def _reset_runtime_state(self) -> None:
        self.filled_orders = 0
        self.failed_orders = 0
        self.skipped_orders = 0
        self.start_time = datetime.now(UTC)
        self.STARTUP_DISK_SNAPSHOT = None

    def _sync_config(self):
        disk_config = cast(dict, self.reader.load_json(self.layout.config_path))
        if self.passed_verified_config is None or self.passed_verified_config == disk_config:
            return

        if disk_config.get("locked", True):
            print("Config mismatch detected: disk config is locked, keeping disk config.")
            return

        self.CONFIG = self.passed_verified_config
        self.STARTING_CASH = self.CONFIG["starting_cash"]
        set_config(self.CONFIG)
        self.writer.overwrite_config(self.passed_verified_config)
        print("Config mismatch detected: overwriting disk config with passed config.")
    
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
            self.STARTUP_DISK_SNAPSHOT = self.reader.save_disk_snapshot()
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
# Portfolio Processing
# ----------------------------------

    def _process(self):
        processing = Processing(run_date=self.run_date, portfolio=self.portfolio, cash=self.cash, 
                                        STARTING_CASH=self.STARTING_CASH, _trade_log_path=self.layout.trade_log_path, 
                                        portfolio_history=self.portfolio_history, 
                                         _position_history_path=self.layout.position_history_path,
                                          _portfolio_history_path=self.layout.portfolio_history_path,
                                        _portfolio_path=self.layout.portfolio_path, _model_path=self._model_path)

        self.pending_trades = processing.processing(self.pending_trades)

        self.filled_orders, self.failed_orders, self.skipped_orders = processing.get_order_status_count()
        self.portfolio = processing.get_portfolio()
        self.cash = processing.get_cash()
                
        self.writer._save_cash(self.cash)
        self.save_orders(self.pending_trades)


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
        
        if not self.portfolio_history.empty:
            if str(self.run_date) in self.portfolio_history["date"]:
                self._instance_is_valid = False
                raise RuntimeError(
                    f"Portfolio snapshot for {self.run_date} already exists. "
                    "Refusing to overwrite historical ledger.")
        
            last_run_date = pd.to_datetime(self.portfolio_history["date"]).max().date()
      
            if self.run_date <= last_run_date:
                raise RuntimeError(
                    f"Backjump Error: Current run_date ({self.run_date}) is on or before "
                    f"the last recorded date ({last_run_date}). Dates must move forward."
                )

        if is_nyse_open(self.run_date):
            try:
                self._process()
                self._save_new_logging_file()
            except Exception as e:
                self._save_new_logging_file(status="FAILURE", error=e)
                self._instance_is_valid = False
                if self.STARTUP_DISK_SNAPSHOT is None:
                    raise RuntimeError("No startup disk snapshot available for rollback; disk may be corrupted.")
                else:
                    self.writer._load_snapshot_to_disk(self.STARTUP_DISK_SNAPSHOT)
                raise SystemError("Processing failed: disk state has been reset to snapshot created on startup.") from e
        else:
            self._save_new_logging_file(status="SKIPPED", error="nyse closed on run date")

# ----------------------------------
# Disk Writing
# ----------------------------------


    def save_deep_research(self, txt: str) -> Path:
        return self.writer.save_deep_research(txt)
    
    def save_daily_update(self, txt: str) -> Path:
        return self.writer.save_daily_update(txt)
    
    def save_orders(self, json_block: dict) -> None:
        self.writer.save_orders(json_block)

    def save_prompt(self, txt: str) -> Path:
        return self.writer.save_prompt(txt)

    def save_additional_log(self, file_name: str, text: str, folder: str="additional_logs", append: bool=False) -> None:
        self.writer.save_additional_log(file_name, text, folder, append)
    

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
            error=str(error),
                )


        return log 
    
    def _save_new_logging_file(self, status: str = "SUCCESS", error: Exception | str = "none"):
        log = self._create_log_dict(status, error)
        self.writer._save_logging_file_to_disk(log)  

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
        return _recent_execution_logs(self.layout.trade_log_path, date=effective_date, look_back=look_back)
    
# ----------------------------------
# graphing
# ----------------------------------
    
    def plot_equity_and_sentiment(self) -> None:
        return plot_equity_and_sentiment(self.layout.portfolio_history_path, self.layout.sentiment_path)
    
    def plot_equity_vs_baseline(self, baseline="^SPX"):
        return plot_equity_vs_baseline(self.layout.portfolio_history_path, baseline_ticker=baseline) 
    
    def plot_equity(self):
        return plot_equity(self.layout.portfolio_history_path)
    

# ----------------------------------
# metrics
# ----------------------------------

    def generate_performance_metrics(self, baseline_ticker = "^SPX") -> dict:
        """
    Compute performance metrics for the current run and persist the result.

    Downloads benchmark data and evaluates portfolio risk, return,
    drawdown, and CAPM metrics against the specified baseline.

    The performance log is appended to the in-memory performance list
    and written to disk as JSON.

    Args:
        baseline_ticker (str): Market benchmark ticker for CAPM and
            relative performance calculations. Defaults to "^SPX".
            Must be accessible via yfinance.

    Returns:
        dict: Performance metrics log containing volatility, Sharpe,
            Sortino, max drawdown, and CAPM metrics against the baseline.
            See `libb.metrics.performance_metrics.total_performance_calculations`
            for full metric definitions.

    Requirements:
        - `process_portfolio()` must have been called at least once
        - portfolio_history.csv must not be empty
        - Portfolio equity must have changed from its initial value
        - Internet access required for benchmark download

    State Interaction:
        Reads:
            - self.layout.portfolio_history_path
            - self.run_date

        Writes:
            - self.performance
            - self.layout.performance_path
        """
        performance_log = total_performance_calculations(self.layout.portfolio_history_path, self.layout.trade_log_path, self.run_date, baseline_ticker)
        self.performance.append(performance_log)
        self.writer.save_performance(self.performance)
        return performance_log
    
    def generate_behavior_metrics(self) -> dict:
        """
        Compute behavioral metrics for the current run and persist the result.

        Analyzes trade execution logs, position history, and portfolio equity
        history to produce a snapshot of LLM decision-making behavior up to
        the current run date.

        The behavior log is appended to the in-memory behavior list and
        written to disk as JSON.

        Returns:
            dict: Behavioral metrics log for the current run. See
                `libb.metrics.behavior_metrics.total_behavioral_metrics`
                for full metric definitions.

        Requirements:
            - `process_portfolio()` must have been called at least once
            - trade_log.csv, position_history.csv, and portfolio_history.csv
            must not be empty

        State Interaction:
            Reads:
                - self.layout.trade_log_path
                - self.layout.position_history_path
                - self.layout.portfolio_history_path
                - self.run_date

            Writes:
                - self.behavior
                - self.layout.behavior_path
        """
        behavior_log = total_behavioral_metrics(self.layout.trade_log_path, self.layout.position_history_path, self.layout.portfolio_history_path, self.run_date)
        self.behavior.append(behavior_log)
        self.writer.save_behavior(self.behavior)
        return behavior_log
    
    def analyze_sentiment(self, text: str, report_type: str="Unknown") -> dict:
        """
    Analyze sentiment for the given text and persist the result.

    Applies the Loughran-McDonald financial sentiment lexicon to the
    provided text and appends the result to the in-memory sentiment
    list and disk.

    Args:
        text (str): Text to analyze. Typically raw model output from
            a daily or weekly research report.
        report_type (str): Identifier describing the source or type of
            the report. Defaults to "Unknown".

    Returns:
        dict: Sentiment log containing subjectivity, polarity, positive
            and negative token counts, total token count, report type,
            and run date. See
            `libb.metrics.sentiment_metrics.analyze_sentiment`
            for full field definitions.

    State Interaction:
        Reads:
            - self.run_date

        Writes:
            - self.sentiment
            - self.layout.sentiment_path
        """
        sentiment_log = analyze_sentiment(text, self.run_date, report_type=report_type)
        self.sentiment.append(sentiment_log)
        self.writer.save_sentiment(self.sentiment)
        return sentiment_log

# ----------------------------------
# market data
# ----------------------------------

    def get_market_data(self, ticker: str, start_date: str | date, end_date: str | date) -> MarketHistoryObject:
        """
        Download market data for a ticker over a date range using configured data sources.
        """
        return download_data_on_given_range(ticker, start_date, end_date)

    def get_market_snapshot(self, ticker: str, date: str | date) -> MarketDataObject:
        """
        Download a single-day market snapshot for a ticker.
        """
        return download_data_on_given_date(ticker, date)