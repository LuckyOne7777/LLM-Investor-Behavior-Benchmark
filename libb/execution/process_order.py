from .buy_logic import process_buy
from .sell_logic import process_sell
from .portfolio_editing import update_stoploss
from .utils import append_log
from ..other.types_file import Order, TradeStatus
import pandas as pd
from pathlib import Path

def process_order(order: Order, portfolio_df: pd.DataFrame, cash: float, trade_log_path: Path) -> tuple[pd.DataFrame, float, TradeStatus]:
    action = str(order["action"])
    ticker = order["ticker"].upper()

    if action == "b":
        return process_buy(order, portfolio_df, cash, trade_log_path)

    if action == "s":
        return process_sell(order, portfolio_df, cash, trade_log_path)

    if action == "u":
        if update_stoploss(portfolio_df, order, trade_log_path):
            return portfolio_df, cash, TradeStatus.FILLED
        else:
            return portfolio_df, cash, TradeStatus.FAILED

    else:
        append_log(trade_log_path, {
            "date": order["date"],
            "ticker": ticker,
            "action": action,
            "status": "FAILED",
            "reason": "UNKNOWN ORDER ACTION"
        })
        return portfolio_df, cash, TradeStatus.FAILED

