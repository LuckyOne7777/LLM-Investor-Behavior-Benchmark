from .portfolio_editing import add_or_update_position
from .utils import append_log, catch_missing_order_data, order_to_trade_schema
from libb.execution.get_market_data import download_data_on_given_date
from libb.other.config_setup import get_config
import pandas as pd
from ..other.types_file import Order
from pathlib import Path

def process_buy(order: Order, portfolio_df: pd.DataFrame, cash: float, trade_log_path: Path) -> tuple[pd.DataFrame, float, bool]:

    CONFIG = get_config()
    slippage = CONFIG["slippage_pct_per_trade"]

    ticker = order["ticker"].upper()
    date = order["date"]
    order_type = order["order_type"].upper()
    shares = int(order["shares"])
    intended_limit_price = order["limit_price"]
    stop_loss = 0 if order["stop_loss"] is None else order["stop_loss"]

    ticker_data = download_data_on_given_date(ticker, date)
    market_low = ticker_data["Low"]
    market_open = ticker_data["Open"]

    # ---------- LIMIT BUY ----------
    if order_type == "LIMIT":

        required_cols = [
            "limit_price",
            "shares",
            "ticker",
        ]
        if not catch_missing_order_data(order, required_cols, trade_log_path):
            return portfolio_df, cash, False

        assert intended_limit_price is not None
        intended_limit_price = float(intended_limit_price)

        if market_low > intended_limit_price:
            reason = f"limit price of {intended_limit_price} not met. (Low: {market_low})"
            trade_dict = order_to_trade_schema(order, executed_price=None, PnL=None,
                                               status="FAILED", reason=reason)
            append_log(trade_log_path, trade_dict)
            return portfolio_df, cash, False

        fill_price = market_open if market_open <= intended_limit_price else intended_limit_price
        fill_price = fill_price * (1 + slippage)
        cost = shares * fill_price

        if cost > cash:
            reason = f"Insufficient cash"
            trade_dict = order_to_trade_schema(order, executed_price=None, PnL=None,
                                               status="FAILED", reason=reason)
            append_log(trade_log_path, trade_dict)
            return portfolio_df, cash, False

        trade_dict = order_to_trade_schema(order, executed_price=fill_price, PnL=None,
                                               status="FILLED", reason="")
        append_log(trade_log_path, trade_dict)

        portfolio_df = add_or_update_position(
            portfolio_df, ticker, shares, fill_price, stop_loss
        )
        cash -= cost

        return portfolio_df, cash, True

    # ---------- MARKET BUY ----------
    elif order_type == "MARKET":

        required_cols = [
            "shares",
            "ticker",
        ]
        if not catch_missing_order_data(order, required_cols, trade_log_path):
            return portfolio_df, cash, False

        fill_price = market_open * (1 + slippage)
        cost = shares * fill_price

        if cost > cash:
            reason = f"Insufficient cash"
            trade_dict = order_to_trade_schema(order, executed_price=None, PnL=None,
                                               status="FAILED", reason=reason)
            append_log(trade_log_path, trade_dict)
            return portfolio_df, cash, False

        trade_dict = order_to_trade_schema(order, executed_price=fill_price, PnL=None,
                                               status="FILLED", reason="")
        append_log(trade_log_path, trade_dict)

        portfolio_df = add_or_update_position(
            portfolio_df, ticker, shares, fill_price, stop_loss
        )
        cash -= cost

        return portfolio_df, cash, True

    else:
        reason = f"ORDER TYPE UNKNOWN"
        trade_dict = order_to_trade_schema(order, executed_price=None, PnL=None,
                                               status="FAILED", reason=reason)
        append_log(trade_log_path, trade_dict)
        return portfolio_df, cash, False