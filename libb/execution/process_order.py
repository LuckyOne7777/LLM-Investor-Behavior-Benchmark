from .buy_logic import process_buy
from .sell_logic import process_sell
from .portfolio_editing import update_stoploss
from .io import append_log
from .types_file import Order
import pandas as pd
from pathlib import Path

def process_order(order: Order, portfolio_df: pd.DataFrame, cash: float, trade_log_path: Path):
    action = str(order["action"])
    ticker = order["ticker"].upper()

    if action == "b":
        return process_buy(order, portfolio_df, cash, trade_log_path)

    if action == "s":
        return process_sell(order, portfolio_df, cash, trade_log_path)

    if action == "u":
        #TODO: Generalize update_stoploss function
        success = update_stoploss(portfolio_df, ticker, order["stop_loss"])
        status = "FILLED" if success else "FAILED"
        reason = "" if success else f"{ticker} not in portfolio"

        append_log(trade_log_path, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "UPDATE_STOPLOSS",
            "Status": status,
            "Reason": reason
        })
        return portfolio_df, cash

    else:
        append_log(trade_log_path, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "UNKNOWN",
            "Status": "FAILED",
            "Reason": "UNKNOWN ORDER TYPE"
        })
        return portfolio_df, cash

