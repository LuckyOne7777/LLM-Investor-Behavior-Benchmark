from .portfolio_editing import reduce_position
from .utils import append_log, catch_missing_order_data, order_to_trade_schema
from libb.execution.get_market_data import download_data_on_given_date
from libb.other.config_setup import get_config
from pathlib import Path
import pandas as pd
from ..other.types_file import Order
from typing import cast 

def process_sell(order: Order, portfolio_df: pd.DataFrame, cash: float, trade_log_path: Path) -> tuple[pd.DataFrame, float, bool]:

    CONFIG = get_config()
    slippage = CONFIG["slippage_pct_per_trade"]

    ticker = order["ticker"].upper()
    order_type = order["order_type"].upper()
    date = order["date"]
    ticker_data = download_data_on_given_date(ticker, date)

    high = ticker_data["High"]
    open_price = ticker_data["Open"]

    shares = int(order["shares"])
    limit_price = float(cast(float, order["limit_price"]))

    row = portfolio_df.loc[portfolio_df["ticker"] == ticker].iloc[0]
    if shares > row["shares"]:
        reason = f"INSUFFICIENT SHARES: REQUESTED {shares}, AVAILABLE {row['shares']}"
        trade_dict = order_to_trade_schema(order, executed_price=None, PnL=None,
                                           status="FAILED", reason=reason)
        append_log(trade_log_path, trade_dict)
        return portfolio_df, cash, False
    
    if order_type == "LIMIT" and high < limit_price:
        reason = f"limit price of {limit_price} not met. (High: {high})"
        trade_dict = order_to_trade_schema(order, executed_price=None, PnL=None,
                                           status="FAILED", reason=reason)
        append_log(trade_log_path, trade_dict)
        return portfolio_df, cash, False

    elif order_type == "LIMIT":
        required_col = ["ticker", "limit_price", "shares"]
        if not catch_missing_order_data(order, required_col, trade_log_path):
                return portfolio_df, cash, False
        fill_price = open_price if open_price >= limit_price else limit_price
        fill_price = fill_price * (1 - slippage)

        proceeds = shares * fill_price
        portfolio_df, buy_price = reduce_position(portfolio_df, ticker, shares)
        cash += proceeds

        pnl = proceeds - (buy_price * shares)
        trade_dict = order_to_trade_schema(order, executed_price=fill_price, PnL=pnl,
                                           status="FILLED", reason="")
        append_log(trade_log_path, trade_dict)
        return portfolio_df, cash, True
            
    elif order_type == "MARKET":
        required_col = ["ticker", "shares"]
        if not catch_missing_order_data(order, required_col, trade_log_path):
                return portfolio_df, cash, False
        
        fill_price = open_price * (1 - slippage)
        proceeds = shares * fill_price
        portfolio_df, buy_price = reduce_position(portfolio_df, ticker, shares)
        cash += proceeds

        pnl = proceeds - (buy_price * shares)
        trade_dict = order_to_trade_schema(order, executed_price=fill_price, PnL=pnl,
                                           status="FILLED", reason="")
        append_log(trade_log_path, trade_dict)
        return portfolio_df, cash, True
    else:
        reason = f"ORDER TYPE UNKNOWN: {order_type}"
        trade_dict = order_to_trade_schema(order, executed_price=None, PnL=None,
                                           status="FAILED", reason=reason)
        append_log(trade_log_path, trade_dict)


        return portfolio_df, cash, False
