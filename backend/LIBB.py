from pathlib import Path 
import pandas as pd
import json
from .execution.types_file import Order
from datetime import date
from .execution.orders import  process_order
import yfinance as yf

class LIBBmodel:
    def __init__(self, model_path, starting_cash = 10_000):
        self.STARTING_CASH = starting_cash
        self.root = Path(model_path)
        self.model_path = model_path
        # directories
        self.portfolio_dir = self.root / "portfolio"
        self.metrics_dir = self.root / "metrics"
        self.research_dir = self.root / "research"

        for dir in [self.root, self.portfolio_dir, self.metrics_dir, self.research_dir]:
            self.ensure_dir(dir)

        # paths in portfolio
        self.portfolio_history_path = self.portfolio_dir / "portfolio_history.csv"
        self.pending_trades_path = self.portfolio_dir / "pending_trades.csv"
        self.portfolio_path = self.portfolio_dir / "portfolio.csv"
        self.trade_log_path = self.portfolio_dir / "trade_log.csv"
        # paths in metrics
        self.behavior_path = self.metrics_dir / "behavior.json"
        self.performance_path = self.metrics_dir / "performance.json"
        self.sentiment_path = self.metrics_dir / "sentiment.json"


        self.portfolio = self._load_csv(self.portfolio_dir / "portfolio.csv")
        self.cash = (float(self.portfolio["cash"].iloc[0]) 
                     if not self.portfolio.empty else self.STARTING_CASH)
        self.portfolio_history = self._load_csv(self.portfolio_dir / "portfolio_history.csv")
        self.trade_log = self._load_csv(self.portfolio_dir / "trade_log.csv")
        self.pending_trades = self._load_csv(self.portfolio_dir / "pending_trades.csv")

        self.performance = self._load_json(self.metrics_dir / "performance.json")
        self.behavior = self._load_json(self.metrics_dir / "behavior.json")
        self.sentiment = self._load_json(self.metrics_dir / "sentiment.json")

    def ensure_dir(self, path: Path):
            path.mkdir(parents=True, exist_ok=True)

    def _load_csv(self, path: Path) -> pd.DataFrame:
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()

    def _load_json(self, path: Path) -> dict:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def process_orders(self):
        for _, order in self.pending_trades.iterrows():
            self.portfolio, self.cash = process_order(order, self.portfolio, 
            self.cash, self.trade_log_path)
        return
    
    def append_portfolio_history(self, date: date | None = None):
        required_cols = {"ticker", "shares", "buy_price", "cost_basis", "stop_loss"}
        missing = required_cols - set(self.portfolio.columns)

        if missing:
            raise RuntimeError(f"Portfolio schema invalid, missing: {missing}")

        if date is None:
            date = pd.Timestamp.now().date()
        if "market_value" not in self.portfolio.columns:
            raise RuntimeError("market_value not computed before portfolio history update")
        market_equity = self.portfolio["market_value"].sum()
        present_total_equity = market_equity + self.cash
        last_total_equity = self.portfolio_history["equity"].iloc[-1]
        if last_total_equity is None:
            return_pct = None
            last_total_equity = None
        else:
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
            raise SystemError(f"Error saving to portfolio_history for {self.model_path}. {e}")
        return