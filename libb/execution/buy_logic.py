from .portfolio_editing import add_or_update_position
from .io import append_log
from .update_data import get_market_data
import pandas as pd
from .types_file import Order
from pathlib import Path

def process_buy(order: Order, portfolio_df: pd.DataFrame, cash: float, trade_log_path: Path) -> tuple[pd.DataFrame, float]:
    ticker = order["ticker"].upper()
    date = order["date"]
    order_type = order["order_type"]
    shares = int(order["shares"])
    intended_limit_price = order["limit_price"]
    stop_loss = 0 if order["stop_loss"] is None else order["stop_loss"]

    ticker_data = get_market_data(ticker, date)
    market_low = ticker_data["Low"]
    market_open = ticker_data["Open"]

    # ---------- LIMIT BUY ----------
    if order_type == "limit":

        required_cols = [
            "limit_price",
            "shares",
            "ticker",
        ]
        missing_cols = []
        for col in required_cols:
            if col not in order or order[col] is None:
                missing_cols.append(col)
        if missing_cols:
            append_log(trade_log_path, {
                "Date": order["date"],
                "Ticker": ticker,
                "Action": "BUY",
                "Status": "FAILED",
                "Reason": f"MISSING ORDER INFO: {missing_cols}"
            })
            return portfolio_df, cash

        

        assert intended_limit_price is not None
        intended_limit_price = float(intended_limit_price)
        # limit buy fails if price never trades at or below limit
        if market_low > intended_limit_price:
            append_log(trade_log_path, {
                "Date": order["date"],
                "Ticker": ticker,
                "Action": "BUY",
                "Status": "FAILED",
                "Reason": f"limit price of {intended_limit_price} not met. (Low: {market_low})"
            })
            return portfolio_df, cash

        # realistic fill price
        fill_price = market_open if market_open <= intended_limit_price else intended_limit_price
        cost = shares * fill_price

        if cost > cash:
            append_log(trade_log_path, {
                "Date": order["date"],
                "Ticker": ticker,
                "Action": "BUY",
                "Status": "FAILED",
                "Reason": "Insufficient cash"
            })
            return portfolio_df, cash

        portfolio_df = add_or_update_position(
            portfolio_df, ticker, shares, fill_price, stop_loss
        )
        cash -= cost

        append_log(trade_log_path, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "BUY",
            "Shares": shares,
            "Price": fill_price,
            "Status": "FILLED",
            "Reason": ""
        })

    # ---------- MARKET BUY ----------
    elif order_type == "market":
        cost = shares * market_open

        if cost > cash:
            append_log(trade_log_path, {
                "Date": order["date"],
                "Ticker": ticker,
                "Action": "BUY",
                "Status": "FAILED",
                "Reason": "Insufficient cash"
            })
            return portfolio_df, cash

        portfolio_df = add_or_update_position(
            portfolio_df, ticker, shares, market_open, stop_loss
        )
        cash -= cost

        append_log(trade_log_path, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "BUY",
            "Shares": shares,
            "Price": market_open,
            "Status": "FILLED",
            "Reason": ""
        })

    else:
        append_log(trade_log_path, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "BUY",
            "Shares": shares,
            "Price": intended_limit_price,
            "Status": "FAILED",
            "Reason": f"ORDER TYPE UNKNOWN: {order_type}"
        })

    return portfolio_df, cash
