from typing import cast

import pandas as pd

from libb.other.types_file import Order, TradeStatus
from libb.execution.utils import append_log, is_nyse_open
from libb.execution.process_order import process_order
from libb.execution.update_data import update_market_value_columns

from typing import Tuple
from datetime import date
from pathlib import Path

# ----------------------------------
# Portfolio Processing
# ----------------------------------

class Processing:
    def __init__(self, *, run_date, portfolio, cash, _trade_log_path, portfolio_history,
                 _position_history_path, _portfolio_history_path, _portfolio_path, _model_path) -> None:
        
        self.run_date: date = run_date

        self.portfolio: pd.DataFrame = portfolio
        self.portfolio_history: pd.DataFrame = portfolio_history
        self.cash: float = cash

        self._trade_log_path: Path = _trade_log_path
        self._position_history_path: Path = _position_history_path
        self._portfolio_history_path: Path = _portfolio_history_path
        self._portfolio_path: Path = _portfolio_path
        self._model_path: Path = _model_path

        self.filled_orders = 0;
        self.failed_orders = 0;        
        
    def _process_orders(self, pending_trades: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """Process all pending orders for the current date.
        Not recommended for workflows; only use `process_portfolio()` for processing."""
        orders = cast(list[Order], pending_trades.get("orders", []))
        unexecuted_trades = {"orders": []}
        if not orders:
            return unexecuted_trades
        for order in orders:
            order_date = pd.Timestamp(order["date"]).date()
            # drop orders in the past
            if order_date < self.run_date:
                append_log(self._trade_log_path, {
                    "date": order["date"],
                    "ticker": order["ticker"],
                    "action": order["action"],
                    "status": "REJECTED",
                    "reason": f"ORDER DATE ({order_date}) IS PAST RUN DATE ({self.run_date})"
                                                    })
                self.failed_orders += 1
                continue
            # drop orders on weekends and holidays
            if not is_nyse_open(order_date):
                append_log(self._trade_log_path, {
                    "date": order["date"],
                    "ticker": order["ticker"],
                    "action": order["action"],
                    "status": "REJECTED",
                    "reason": f"NYSE CLOSED ON ORDER DATE"
                                                    })
                self.failed_orders += 1
                continue
            if not isinstance(order["shares"], int) and order["shares"] is not None:
                append_log(self._trade_log_path, {
                    "date": order["date"],
                    "ticker": order["ticker"],
                    "action": order["action"],
                    "status": "FAILED",
                    "reason": f"SHARES NOT INT: ({order['shares']})"
                                                    })
                self.failed_orders += 1
                continue
            if order_date == self.run_date:
                self.portfolio, self.cash, status = process_order(order, self.portfolio, 
                self.cash, self._trade_log_path)

            else:
                unexecuted_trades["orders"].append(order)
                status = TradeStatus.SKIPPED
            match status:
                case TradeStatus.FILLED:
                    self.filled_orders += 1
                case TradeStatus.FAILED:
                    self.failed_orders += 1
                case TradeStatus.SKIPPED:
                    self.skipped_orders += 1
        # keep any unexecuted trades, completely reset otherwise
        if not unexecuted_trades["orders"]:
            pending_trades = {"orders": []}
        else:
            pending_trades = unexecuted_trades
        return pending_trades
    
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
            return_pct = round(((present_total_equity - last_total_equity) / last_total_equity) * 100, 2)
        log = {
        "date": str(self.run_date),
        "cash": round(self.cash, 2),
        "equity": round(present_total_equity, 2),
        "return_pct": return_pct,
        "positions_value": round(market_equity, 2),
        }
        try:
            append_log(self._portfolio_history_path, log)
        except Exception as e:
            raise SystemError(f"""Error saving to portfolio_history for {self._model_path}. 
                              You may have called 'reset_run()` without calling `ensure_file_system()` immediately after.""") from e
        return
    def _update_portfolio_market_data(self) -> None:
        """Update market portfolio value and cash. Save new values to disk."""
        self.portfolio = update_market_value_columns(self.portfolio, date=self.run_date)

        self.portfolio.to_csv(self._portfolio_path, index=False)
        
        required_cols = [
            "ticker",
            "shares",
            "cost_basis",
            "market_price",
            "market_value",
            "unrealized_pnl",
            ]

        assert self.portfolio[required_cols].notnull().all().all(), (
        "Null values found in required portfolio columns:\n"
        f"{self.portfolio[required_cols]}")

        return

    def processing(self, pending_trades: dict[str, list[dict]]) -> Tuple[dict[str, list[dict]], float]:
        unexecuted_trades = self._process_orders(pending_trades)
        self._update_portfolio_market_data()
        self._append_portfolio_history()
        self._append_position_history()
        return unexecuted_trades, self.cash
    
    def get_order_status_count(self) -> Tuple[int, int]:
        return self.filled_orders, self.failed_orders
    
    def get_portfolio(self) -> pd.DataFrame:
        return self.portfolio
            