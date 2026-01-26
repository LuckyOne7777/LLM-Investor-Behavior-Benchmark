from pathlib import Path 
import pandas as pd
import json
from datetime import date, datetime
from libb.execution.utils import append_log, is_nyse_open
from libb.execution.process_order import  process_order
from libb.metrics.sentiment_metrics import analyze_sentiment
from libb.execution.update_data import update_market_value_columns
from libb.user_data.news import _get_macro_news, _get_portfolio_news
from libb.user_data.logs import _recent_execution_logs
from shutil import rmtree
from dataclasses import dataclass
from libb.execution.types_file import Order
from typing import cast
from copy import deepcopy

@dataclass (frozen=True)
class ModelSnapshot:
    cash: float

    portfolio_history: pd.DataFrame
    portfolio: pd.DataFrame
    trade_log: pd.DataFrame
    position_history: pd.DataFrame

    pending_trades: dict[str, list[dict]]
    performance: list[dict]
    behavior: list[dict]
    sentiment: list[dict]

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

        self.STARTING_CASH: float = starting_cash
        self._root: Path = Path(model_path)
        self._model_path: str = str(model_path)
        self.run_date: date = run_date

        # directories
        self._portfolio_dir: Path = self._root / "portfolio"
        self._metrics_dir: Path = self._root / "metrics"
        self._research_dir: Path = self._root / "research"

        self._deep_research_file_folder_path: Path = self._research_dir / "deep_research"
        self._daily_reports_file_folder_path: Path = self._research_dir / "daily_reports"

        # paths in portfolio
        self._portfolio_history_path: Path = self._portfolio_dir / "portfolio_history.csv"
        self._pending_trades_path: Path = self._portfolio_dir / "pending_trades.json"
        self._portfolio_path: Path = self._portfolio_dir / "portfolio.csv"
        self._trade_log_path: Path = self._portfolio_dir / "trade_log.csv"
        self._position_history_path: Path = self._portfolio_dir / "position_history.csv"

        # paths in metrics
        self._behavior_path: Path = self._metrics_dir / "behavior.json"
        self._performance_path: Path = self._metrics_dir / "performance.json"
        self._sentiment_path: Path = self._metrics_dir / "sentiment.json"

        self.ensure_file_system()

        self.portfolio: pd.DataFrame = self._load_csv(self._portfolio_path)
        self.cash: float = (float(self.portfolio["cash"].iloc[0]) 
                     if not self.portfolio.empty else self.STARTING_CASH)
        self.portfolio_history: pd.DataFrame = self._load_csv(self._portfolio_history_path)
        self.trade_log: pd.DataFrame = self._load_csv(self._trade_log_path)
        self.position_history: pd.DataFrame = self._load_csv(self._position_history_path)

        self.pending_trades: dict[str, list[dict]] = self._load_orders_dict(self._pending_trades_path)
        self.performance: list[dict] = self._load_json(self._performance_path)
        self.behavior: list[dict] = self._load_json(self._behavior_path)
        self.sentiment: list[dict] = self._load_json(self._sentiment_path)

        self.STARTUP_DISK_SNAPSHOT = self._save_disk_snapshot()
        assert self.STARTUP_DISK_SNAPSHOT is not None


# ----------------------------------
# Filesystem & Persistence
# ----------------------------------

    def ensure_file_system(self):
        "Create and set up all files/folders needed for processing and metrics. Automatically called during construction."
        for dir in [self._root, self._portfolio_dir, self._metrics_dir, self._research_dir, self._daily_reports_file_folder_path, 
                    self._deep_research_file_folder_path]:
            self._ensure_dir(dir)

        # portfolio files
        self._ensure_file(self._portfolio_history_path, "date,equity,cash,positions_value,return_pct\n")
        self._ensure_file(self._pending_trades_path, '{"orders": []}')
        self._ensure_file(self._portfolio_path, "ticker,shares,buy_price,cost_basis,stop_loss,market_price,market_value,unrealized_pnl,cash\n")
        self._ensure_file(self._trade_log_path, "date,ticker,action,shares,price,cost_basis,PnL,rationale,confidence,status,reason\n")
        self._ensure_file(self._position_history_path, "date,ticker,shares,avg_cost,stop_loss,market_price,market_value,unrealized_pnl,cash\n")

        # metrics files
        self._ensure_file(self._behavior_path, "[]")
        self._ensure_file(self._performance_path, "[]")
        self._ensure_file(self._sentiment_path, "[]")
        return
    
    def reset_run(self, cli_check: bool = True, auto_ensure: bool = False) -> None:
        """
        Delete all files within the given root.

        If ensure_file_system() is not called afterward, processing will
        silently fail or raise an error.

        Args:
            cli_check (bool): Require interactive confirmation before deleting files.
                Defaults to True.

            auto_ensure (bool): Automatically calls `ensure_file_system()` after deletion
                Defaults to False.
        """
        root = self._root.resolve()
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


    def _load_csv(self, path: Path) -> pd.DataFrame:
        """Helper for loading CSV at a given path. Return empty DataFrame for invalid paths."""
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()

    def _load_json(self, path: Path) -> list[dict]:
        "Helper for loading JSON files at a given path. Return empty dict for invalid paths."
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return []
    
    def _load_orders_dict(self, path: Path) -> dict[str, list[dict]]:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {"orders": []}

    def _override_json_file(self, data: list[dict] | dict[str, list[dict]], path: Path) -> None:
        with open(path, "w") as file:
            json.dump(data, file, indent=2)
        return
    
    def _override_csv_file(self, df: pd.DataFrame, path: Path) -> None:
        df.to_csv(path, mode="w", header=True, index=False)
        return
    
    def _save_disk_snapshot(self) -> ModelSnapshot:
        "Function for saving a disk snapshot."
        return ModelSnapshot(
        cash= (float(self.portfolio["cash"].iloc[0]) 
                     if not self.portfolio.empty else self.STARTING_CASH),

        portfolio= self._load_csv(self._portfolio_path),
        portfolio_history= self._load_csv(self._portfolio_history_path),
        trade_log= self._load_csv(self._trade_log_path),
        position_history=self._load_csv(self._position_history_path),
        pending_trades= self._load_orders_dict(self._pending_trades_path),

        performance= self._load_json(self._performance_path),
        behavior= self._load_json(self._behavior_path),
        sentiment= self._load_json(self._sentiment_path),
        )
    def _load_snapshot_to_disk(self, snapshot: ModelSnapshot) -> None:
        """Override CSV and JSON artifacts based on prior disk snapshot."""
        self._override_csv_file(snapshot.portfolio, self._portfolio_path)
        self._override_csv_file(snapshot.portfolio_history, self._portfolio_history_path)
        self._override_csv_file(snapshot.trade_log, self._trade_log_path)
        self._override_csv_file(snapshot.position_history, self._position_history_path)

        self._override_json_file(snapshot.performance, self._performance_path)
        self._override_json_file(snapshot.sentiment, self._sentiment_path)
        self._override_json_file(snapshot.pending_trades, self._pending_trades_path)
        self._override_json_file(snapshot.behavior, self._behavior_path)
        return

# ----------------------------------
# Portfolio Processing
# ----------------------------------


    def _process_orders(self) -> None:
        """Process all pending orders for the current date.
        Not recommended for workflows; only use `process_portfolio()` for processing."""
        orders = cast(list[Order], self.pending_trades.get("orders", []))
        unexecuted_trades = {"orders": []}
        if not orders:
            return
        for order in orders:
            order_date = pd.Timestamp(order["date"]).date()
            # drop orders in the past
            if order_date < self.run_date:
                append_log(self._trade_log_path, {
                    "date": order["date"],
                    "ticker": order["ticker"],
                    "action": order["action"],
                    "status": "FAILED",
                    "reason": f"ORDER DATE ({order_date}) IS PAST RUN DATE ({self.run_date})"
                                                    })
                continue
            if not isinstance(order["shares"], int) and order["shares"] is not None:
                append_log(self._trade_log_path, {
                    "date": order["date"],
                    "ticker": order["ticker"],
                    "action": order["action"],
                    "status": "FAILED",
                    "reason": f"SHARES NOT INT: ({order['shares']})"
                                                    })
                continue
            if order_date == self.run_date:
                self.portfolio, self.cash = process_order(order, self.portfolio, 
                self.cash, self._trade_log_path)
            else:
                unexecuted_trades["orders"].append(order)
        # keep any unexecuted trades, completely reset otherwise
        if not unexecuted_trades["orders"]:
            self.pending_trades = {"orders": []}
        else:
            self.pending_trades = unexecuted_trades
        self.save_orders(self.pending_trades)
        return
    
    def _append_position_history(self) -> None:
        "Append position history CSV based on portfolio data."
        portfolio_copy = self.portfolio.copy()
        portfolio_copy["date"] = self.run_date
        assert (portfolio_copy["shares"] != 0).all() 
        portfolio_copy["avg_cost"] = portfolio_copy["cost_basis"] / portfolio_copy["shares"]
        portfolio_copy.drop(columns=["buy_price", "cost_basis"], inplace=True)
        append_log(self._position_history_path, portfolio_copy)
        return
    
    def _append_portfolio_history(self) -> None:
        """Append portfolio history CSV based on portfolio data."""

        defaults = {
            "ticker": "",
            "shares": 0,
            "buy_price": 0.0,
            "cost_basis": 0.0,
            "stop_loss": 0.0,
                }

        for col, default in defaults.items():
            if col not in self.portfolio.columns:
                self.portfolio[col] = default

        if "market_value" not in self.portfolio.columns and not self.portfolio.empty:
            raise RuntimeError("`market_value` not computed before portfolio history update.")
        market_equity = self.portfolio["market_value"].sum()
        present_total_equity = market_equity + self.cash
        if self.portfolio_history.empty:
            return_pct = None
            last_total_equity = None
        else:
            last_total_equity = self.portfolio_history["equity"].iloc[-1]
            return_pct = (present_total_equity / last_total_equity) - 1
        log = {
        "date": self.run_date,
        "cash": self.cash,
        "equity": present_total_equity,
        "return_pct": return_pct,
        "positions_value": market_equity,
        }
        try:
            append_log(self._portfolio_history_path, log)
        except Exception as e:
            raise SystemError(f"""Error saving to portfolio_history for {self._model_path}. 
                              You may have called 'reset_run()` without calling `ensure_file_system()` immediately after.""") from e
        return
    def _update_portfolio_market_data(self) -> None:
        """Update market portfolio values and save to disk."""
        self.portfolio = update_market_value_columns(self.portfolio, self.cash, date=self.run_date)
        self.portfolio.to_csv(self._portfolio_path, index=False)
        return
    
    def _catch_processing_errors(self) -> None:
        """
        Process portfolio and reset to prior disk state on errors.
        """
        try:
            self._process_orders()
            self._update_portfolio_market_data()
            self._append_portfolio_history()
            self._append_position_history()
        except Exception as e:
            self._load_snapshot_to_disk(self.STARTUP_DISK_SNAPSHOT)
            raise SystemError("Processing failed: disk state has been reset to snapshot created on startup.") from e

    def process_portfolio(self) -> None:
        "Wrapper for all portfolio processing."
        self._catch_processing_errors()

# ----------------------------------
# Saving Logs
# ----------------------------------


    def save_deep_research(self, txt: str) -> Path:
        """Save given text to `deep_research` folder. Returns the file path after completion.
        The file naming format is `deep_research - {date}.txt`. """
        deep_research_name = Path(f"deep_research - {self.run_date}.txt")
        full_path =  self._deep_research_file_folder_path / deep_research_name
        with open(full_path, "w", encoding="utf-8") as file:
            file.write(txt)
            file.close()
        return full_path
    
    def save_daily_update(self, txt: str) -> Path:
        """Save the given text to the `daily_reports` folder.

            Returns the file path after completion.
            The file naming format is `daily_update - {date}.txt`.
        """
        daily_updates_file_name = Path(f"daily_update - {self.run_date}.txt")
        full_path = self._daily_reports_file_folder_path / daily_updates_file_name
        with open(full_path, "w", encoding="utf-8") as file:
            file.write(txt)
        return full_path
    
    def save_orders(self, json_block: dict) -> None:
        """
        Save the given JSON-serializable data to `pending_trades.json`.
        """
        with open(self._pending_trades_path, "w") as file:
            try:
                json.dump(json_block, file, indent=2)
            except Exception as e:
                raise RuntimeError(f"Error while saving JSON block to `pending_trades.json`. ({e})")
        return

    def save_additonal_log(self, file_name: str, text: str, folder: str="additional_logs", append: bool=False) -> None:
        """
    Save text to a log file inside the research directory.

    Args:
        file_name (`str`, required): Name of the file to write to.
        text (`str`): Text content to save.
        folder (`str`, optional): Subfolder inside research_dir where the file
            will be stored. Defaults to "additional_logs".
        append (`bool`, optional): If True, append to the file; otherwise,
            overwrite it. Defaults to False.
        """
        path = Path(self._research_dir / folder / file_name)
        path.parent.mkdir(exist_ok=True, parents=True)
        mode = "w" if not append else "a"
        with open(path, mode, encoding="utf-8") as file:
            file.write(text)
            file.close()
        return

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
    
    
    