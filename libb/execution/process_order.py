from .buy_logic import process_buy
from .sell_logic import process_sell
from .portfolio_editing import update_stoploss
from .utils import append_log
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
        update_stoploss(portfolio_df, order, trade_log_path)
        return portfolio_df, cash

    else:
        append_log(trade_log_path, {
            "date": order["date"],
            "ticker": ticker,
            "action": action,
            "status": "FAILED",
            "reason": "UNKNOWN ORDER ACTION"
        })
        return portfolio_df, cash

