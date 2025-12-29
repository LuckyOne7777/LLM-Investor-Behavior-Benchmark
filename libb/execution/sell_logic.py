from .portfolio_editing import reduce_position
from .utils import append_log, catch_missing_order_data
from .update_data import get_market_data
from pathlib import Path
import pandas as pd
from .types_file import Order
from typing import cast 

def process_sell(order: Order, portfolio_df: pd.DataFrame, cash: float, trade_log_path: Path) -> tuple[pd.DataFrame, float]:
    ticker = order["ticker"].upper()
    order_type = order["order_type"]
    ticker_data = get_market_data(ticker)

    high = ticker_data["High"]
    open_price = ticker_data["Open"]

    shares = int(order["shares"])
    limit_price = float(cast(float, order["limit_price"]))

    row = portfolio_df.loc[portfolio_df["ticker"] == ticker].iloc[0]
    if shares > row["shares"]:
        append_log(trade_log_path, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "SELL",
            "Status": "FAILED",
            "Reason": f"INSUFFICIENT SHARES: REQUESTED {shares}, AVAILABLE {row['shares']}"
        })
        return portfolio_df, cash
    
    if order_type == "limit" and high < limit_price:

        append_log(trade_log_path, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "SELL",
            "Status": "FAILED",
            "Reason": f"limit price of {limit_price} not met. (High: {high})"
        })
        return portfolio_df, cash

    elif order_type == "limit":
        required_col = ["ticker", "limit_price", "shares"]
        if not catch_missing_order_data(order, required_col, trade_log_path):
                return portfolio_df, cash
        fill_price = open_price if open_price >= limit_price else limit_price
        proceeds = shares * fill_price
        portfolio_df, buy_price = reduce_position(portfolio_df, ticker, shares)
        cash += proceeds

        pnl = proceeds - (buy_price * shares)

        append_log(trade_log_path, {
                "Date": order["date"],
                "Ticker": ticker,
                "Action": "SELL",
                "Shares": shares,
                "Price": fill_price,
                "PnL": pnl,
                "Status": "FILLED",
                "Reason": ""
    })
            
    elif order_type == "market":
        required_col = ["ticker", "shares"]
        if not catch_missing_order_data(order, required_col, trade_log_path):
                return portfolio_df, cash
        
        proceeds = shares * open_price
        portfolio_df, buy_price = reduce_position(portfolio_df, ticker, shares)
        cash += proceeds

        pnl = proceeds - (buy_price * shares)
        append_log(trade_log_path, {
                "Date": order["date"],
                "Ticker": ticker,
                "Action": "SELL",
                "Shares": shares,
                "Price": open_price,
                "PnL": pnl,
                "Status": "FILLED",
                "Reason": ""
        })
    else:
          append_log(trade_log_path, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "SELL",
            "Status": "FAILED",
            "Reason": f"ORDER TYPE UNKNOWN: {order_type}"
        })


    return portfolio_df, cash
