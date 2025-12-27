from pathlib import Path 
import pandas as pd
import json
from datetime import date
from .execution.process_order import  process_order
from .metrics.sentiment_metrics import analyze_sentiment
from .execution.update_data import update_market_value_column
from shutil import rmtree
from datetime import datetime

class LIBBmodel:
    def __init__(self, model_path: Path | str, starting_cash: float = 10_000, date: str | date = pd.Timestamp.now().date()):
        self.STARTING_CASH: float = starting_cash
        self.root: Path = Path(model_path)
        self.model_path: str = str(model_path)
        # directories
        self.portfolio_dir: Path = self.root / "portfolio"
        self.metrics_dir: Path = self.root / "metrics"
        self.research_dir: Path = self.root / "research"

        self.deep_research_file_folder_path: Path = self.research_dir / "deep_research"
        self.daily_reports_file_folder_path: Path = self.research_dir / "daily_reports"

        # paths in portfolio
        self.portfolio_history_path: Path = self.portfolio_dir / "portfolio_history.csv"
        self.pending_trades_path: Path = self.portfolio_dir / "pending_trades.json"
        self.portfolio_path: Path = self.portfolio_dir / "portfolio.csv"
        self.trade_log_path: Path = self.portfolio_dir / "trade_log.csv"
        self.position_history_path: Path = self.portfolio_dir / "position_history.csv"

        # paths in metrics
        self.behavior_path: Path = self.metrics_dir / "behavior.json"
        self.performance_path: Path = self.metrics_dir / "performance.json"
        self.sentiment_path: Path = self.metrics_dir / "sentiment.json"

        self.portfolio: pd.DataFrame = self._load_csv(self.portfolio_dir / "portfolio.csv")
        self.cash: float = (float(self.portfolio["cash"].iloc[0]) 
                     if not self.portfolio.empty else self.STARTING_CASH)
        self.portfolio_history: pd.DataFrame = self._load_csv(self.portfolio_dir / "portfolio_history.csv")
        self.trade_log: pd.DataFrame = self._load_csv(self.portfolio_dir / "trade_log.csv")

        self.pending_trades: dict = self._load_json(self.portfolio_dir / "pending_trades.json")

        self.performance: dict = self._load_json(self.metrics_dir / "performance.json")
        self.behavior: dict = self._load_json(self.metrics_dir / "behavior.json")
        self.sentiment: dict = self._load_json(self.metrics_dir / "sentiment.json")

        self.ensure_file_system()

    def ensure_file_system(self):
        for dir in [self.root, self.portfolio_dir, self.metrics_dir, self.research_dir, self.daily_reports_file_folder_path, 
                    self. deep_research_file_folder_path]:
            self.ensure_dir(dir)

        # portfolio files
        self.ensure_file(self.portfolio_history_path, "date,equity,cash,positions_value,return_pct\n")
        self.ensure_file(self.pending_trades_path, '{"orders": []}')
        self.ensure_file(self.portfolio_path, "ticker,shares,buy_price,cost_basis,stop_loss,market_price,market_value,unrealized_pnl,cash\n")
        #TODO: make remove capital letters for columns
        self.ensure_file(self.trade_log_path, "Date,Ticker,Action,Shares,Price,Cost Basis,PnL,Rationale,Confidence,Status,Reason\n")
        self.ensure_file(self.position_history_path, "date,ticker,shares,avg_cost,stop_loss,market_price,market_value,unrealized_pnl,cash\n")

        # metrics files
        self.ensure_file(self.behavior_path, "[]")
        self.ensure_file(self.performance_path, "[]")
        self.ensure_file(self.sentiment_path, "[]")
        return
    
    def reset_run(self, cli_check: bool= True) -> None:
        if cli_check:
            user_decision = None
            while user_decision not in {"y", "n"}:
                user_decision = input(f"Warning: reset_run() is about to delete all files and folders within {self.root}. Proceed? (y/n) ")
            if user_decision == "n":
                raise RuntimeError("Please remove reset_run call from your workflow.")
        if self.root in (Path("/"), Path("C:/")):
                    raise RuntimeError(f"Cannot delete root given: {self.root}")
        for child in self.root.iterdir():
            if child.is_dir():
                rmtree(child)
            else:
                child.unlink()
        return

    def ensure_dir(self, path: Path) -> None:
            path.mkdir(parents=True, exist_ok=True)

    def ensure_file(self, path: Path, default_content: str = "") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(default_content, encoding="utf-8")


    def _load_csv(self, path: Path) -> pd.DataFrame:
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()

    def _load_json(self, path: Path) -> dict:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def process_orders(self) -> None:
        orders = self.pending_trades.get("orders", [])
        unexecuted_trades = {"orders": []}
        if not orders:
            return
        for order in orders:
            order_date = pd.Timestamp(order["date"]).date()
            if order_date == pd.Timestamp.now().date():
                self.portfolio, self.cash = process_order(order, self.portfolio, 
                self.cash, self.trade_log_path)
            else:
                unexecuted_trades["orders"].append(order)
        # keep any unexecuted trades, completely reset otherwise
        if not unexecuted_trades["orders"]:
            self.pending_trades = {"orders": []}
        else:
            self.pending_trades = unexecuted_trades
        self.save_orders(self.pending_trades)
        return
    
    def append_position_history(self) -> None:
        portfolio_copy = self.portfolio.copy()
        portfolio_copy["date"] = pd.Timestamp.now().date()
        portfolio_copy["avg_cost"] = portfolio_copy["cost_basis"] / portfolio_copy["shares"]
        portfolio_copy.drop(columns=["buy_price", "cost_basis"], inplace=True)
        portfolio_copy.to_csv(self.position_history_path, mode="a", header= not 
            self.position_history_path.exists(), index=False)
        return
    
    def append_portfolio_history(self, date: date | None = None) -> None:
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

        if date is None:
            date = pd.Timestamp.now().date()
        if "market_value" not in self.portfolio.columns and not self.portfolio.empty:
            raise RuntimeError("market_value not computed before portfolio history update")
        market_equity = self.portfolio["market_value"].sum()
        present_total_equity = market_equity + self.cash
        if self.portfolio_history.empty:
            return_pct = None
            last_total_equity = None
        else:
            last_total_equity = self.portfolio_history["equity"].iloc[-1]
            return_pct = (present_total_equity / last_total_equity) - 1
        log = pd.DataFrame([{
        "date": date,
        "cash": self.cash,
        "equity": present_total_equity,
        "return_pct": return_pct,
        "positions_value": market_equity,
        }])
        try:
             log.to_csv(self.portfolio_history_path, mode="a", header= not 
            self.portfolio_history_path.exists(), index=False)
        except Exception as e:
            raise SystemError(f"""Error saving to portfolio_history for {self.model_path}. ({e}) 
                              You may have called 'reset_run()' without calling 'ensure_file_system()' immediately after.""")
        return
    def update_portfolio_market_data(self) -> None:
        update_market_value_column(self.portfolio, self.cash)
        return
    
    def process_portfolio(self) -> None:
        self.process_orders()
        self.update_portfolio_market_data()
        self.append_portfolio_history()
        self.append_position_history()

    def save_deep_research(self, txt: str) -> Path:
        deep_research_name = Path(f"deep_research - {pd.Timestamp.now().date()}.txt")
        full_path =  self.deep_research_file_folder_path / deep_research_name
        with open(full_path, "w") as file:
            file.write(txt)
            file.close()
        return full_path
    
    def save_daily_update(self, txt: str) -> Path:
        DAILY_UPDATES_FILE_NAME = Path(f"daily_update - {pd.Timestamp.now().date()}.txt")
        full_path = self.daily_reports_file_folder_path / DAILY_UPDATES_FILE_NAME
        with open(full_path, "w") as file:
            file.write(txt)
            file.close()
        return full_path
    
    def save_orders(self, json_block: str) -> None:
        # override orders each day
        with open(self.pending_trades_path, "w") as file:
            json.dump(json_block, file, indent=2)
            file.close()
        return

    def save_additonal_log(self, file_name: str, text: str, folder: str="additional_logs", append: bool=False) -> None:
        path = Path(self.research_dir / folder / file_name)
        path.parent.mkdir(exist_ok=True, parents=True)
        mode = "w" if not append else "a"
        with open(path, mode, encoding="utf-8") as file:
            file.write(text)
            file.close()
        return
    
    def analyze_sentiment(self, text: str, report_type: str="Unknown"):
        log = analyze_sentiment(text, report_type=report_type)
        self.sentiment.append(log)
        with open(self.sentiment_path, "w") as file:
            json.dump(self.sentiment, file, indent=2)
        return log
