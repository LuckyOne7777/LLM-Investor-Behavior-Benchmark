from pathlib import Path 
import pandas as pd
import json
from datetime import date 

class LIBBmodel:
    def __init__(self, model_path, starting_cash = 10_000):
        self.STARTING_CASH = starting_cash
        self.root = Path(model_path)
        self.model_path = model_path
        # directories
        self.portfolio_dir = self.root / "portfolio"
        self.metrics_dir = self.root / "metrics"
        self.research_dir = self.root / "research"
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
        self.portfolio_history = self._load_csv(self.portfolio_dir / "portfolio_history.csv")
        self.trade_log = self._load_csv(self.portfolio_dir / "trade_log.csv")

        self.performance = self._load_json(self.metrics_dir / "performance.json")
        self.behavior = self._load_json(self.metrics_dir / "behavior.json")
        self.sentiment = self._load_json(self.metrics_dir / "sentiment.json")

    def _load_csv(self, path: Path) -> pd.DataFrame:
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()

    def _load_json(self, path: Path) -> dict:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {}
    def append_portfolio_history(self, date: date | None = None):
        if date is None:
            date = pd.Timestamp.now().date()
        cash = self.portfolio["cash"].astype(float).unique()
        if len(cash) != 1:
            raise ValueError(f"Multiple cash values found. Check portfolio.csv for {self.model_path}.")
        cash = cash[0]
        market_equity = self.portfolio["market_value"].sum()
        present_total_equity = market_equity + cash
        last_total_equity = self.portfolio_history["equity"].iloc[-1]
        if last_total_equity is None:
            return_pct = None
        else:
            return_pct = (present_total_equity / last_total_equity) - 1
        log = pd.DataFrame([{
        "date": date,
        "cash": cash,
        "equity": present_total_equity,
        "return_pct": return_pct,
        "positions_value": market_equity,
        }])
        try:
             log.to_csv(self.portfolio_history_path, mode="a", header= not 
            self.portfolio_history.exists(), index=False)
        except Exception as e:
            raise SystemError(f"Error saving to portfolio_history for {self.model_path}. {e}")
        return