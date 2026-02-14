from .portfolio_editing import reduce_position
from .utils import append_log, catch_missing_order_data
from .update_data import get_market_data
from pathlib import Path
import pandas as pd
from ..other.types_file import Order
from typing import cast 

def process_sell(order: Order, portfolio_df: pd.DataFrame, cash: float, trade_log_path: Path) -> tuple[pd.DataFrame, float, bool]:
    ticker = order["ticker"].upper()
    order_type = order["order_type"]
    date = order["date"]
    ticker_data = get_market_data(ticker, date)

    high = ticker_data["High"]
    open_price = ticker_data["Open"]

    shares = int(order["shares"])
    limit_price = float(cast(float, order["limit_price"]))

    row = portfolio_df.loc[portfolio_df["ticker"] == ticker].iloc[0]
    if shares > row["shares"]:
        append_log(trade_log_path, {
            "date": order["date"],
            "ticker": ticker,
            "action": "SELL",
            "status": "FAILED",
            "reason": f"INSUFFICIENT SHARES: REQUESTED {shares}, AVAILABLE {row['shares']}"
        })
        return portfolio_df, cash, False
    
    if order_type == "limit" and high < limit_price:

        append_log(trade_log_path, {
            "date": order["date"],
            "ticker": ticker,
            "action": "SELL",
            "status": "FAILED",
            "reason": f"limit price of {limit_price} not met. (High: {high})"
        })
        return portfolio_df, cash, False

    elif order_type == "limit":
        required_col = ["ticker", "limit_price", "shares"]
        if not catch_missing_order_data(order, required_col, trade_log_path):
                return portfolio_df, cash, False
        fill_price = open_price if open_price >= limit_price else limit_price
        proceeds = shares * fill_price
        portfolio_df, buy_price = reduce_position(portfolio_df, ticker, shares)
        cash += proceeds

        pnl = proceeds - (buy_price * shares)

        append_log(trade_log_path, {
                "date": order["date"],
                "ticker": ticker,
                "action": "SELL",
                "shares": shares,
                "price": fill_price,
                "PnL": round(pnl, 2),
                "status": "FILLED",
                "reason": ""
    })
        return portfolio_df, cash, True
            
    elif order_type == "market":
        required_col = ["ticker", "shares"]
        if not catch_missing_order_data(order, required_col, trade_log_path):
                return portfolio_df, cash, False
        
        proceeds = shares * open_price
        portfolio_df, buy_price = reduce_position(portfolio_df, ticker, shares)
        cash += proceeds

        pnl = proceeds - (buy_price * shares)
        append_log(trade_log_path, {
                "date": order["date"],
                "ticker": ticker,
                "action": "SELL",
                "shares": shares,
                "price": open_price,
                "PnL": round(pnl, 2),
                "status": "FILLED",
                "reason": ""
        })
        return portfolio_df, cash, True
    else:
        append_log(trade_log_path, {
            "date": order["date"],
            "ticker": ticker,
            "action": "SELL",
            "status": "FAILED",
            "reason": f"ORDER TYPE UNKNOWN: {order_type}"
        })


        return portfolio_df, cash, False
