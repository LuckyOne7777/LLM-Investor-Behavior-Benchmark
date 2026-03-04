from .buy_logic import process_buy
from .sell_logic import process_sell
from .portfolio_editing import update_stoploss
from .utils import append_log, order_to_trade_schema
from ..other.types_file import Order, TradeStatus
import pandas as pd
from pathlib import Path

def process_order(order: Order, portfolio_df: pd.DataFrame, cash: float, trade_log_path: Path) -> tuple[pd.DataFrame, float, TradeStatus]:
    action = str(order["action"])

    if action == "b":
        portfolio_df, cash, status = process_buy(order, portfolio_df, cash, trade_log_path)

        if status:
            return portfolio_df, cash, TradeStatus.FILLED
        else: 
            return portfolio_df, cash, TradeStatus.FAILED

    if action == "s":
        portfolio_df, cash, status = process_sell(order, portfolio_df, cash, trade_log_path)

        if status:
            return portfolio_df, cash, TradeStatus.FILLED
        else: 
             return portfolio_df, cash, TradeStatus.FAILED

    if action == "u":
        if update_stoploss(portfolio_df, order, trade_log_path):
            return portfolio_df, cash, TradeStatus.FILLED
        else:
            return portfolio_df, cash, TradeStatus.FAILED

    else:
        reason = "UNKNOWN ORDER ACTION"
        trade_dict = order_to_trade_schema(order, executed_price=None, PnL=None,
                                           status="FAILED", reason=reason)
        append_log(trade_log_path, trade_dict)
        return portfolio_df, cash, TradeStatus.FAILED

