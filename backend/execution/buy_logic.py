from .portfolio_editing import add_or_update_position
from .io import append_log
from .update_data import get_market_data
import pandas as pd
from .types_file import Order
from pathlib import Path

def process_buy(order: Order, portfolio_df: pd.DataFrame, cash: float, trade_log_path: Path) -> tuple[pd.DataFrame, float]:
    ticker = order["ticker"].upper()
    order_type = order["order_type"]
    shares = int(order["shares"])
    limit_price = float(order["limit_price"])
    stop_loss = order.get("stop_loss")

    ticker_data = get_market_data(ticker)
    low = ticker_data["Low"]
    open_price = ticker_data["Open"]

    # ---------- LIMIT BUY ----------
    if order_type == "limit":
        # limit buy fails if price never trades at or below limit
        if low > limit_price:
            append_log(trade_log_path, {
                "Date": order["date"],
                "Ticker": ticker,
                "Action": "BUY",
                "Status": "FAILED",
                "Reason": f"limit price of {limit_price} not met. (Low: {low})"
            })
            return portfolio_df, cash

        # realistic fill price
        fill_price = open_price if open_price <= limit_price else limit_price
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
        cost = shares * open_price

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
            portfolio_df, ticker, shares, open_price, stop_loss
        )
        cash -= cost

        append_log(trade_log_path, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "BUY",
            "Shares": shares,
            "Price": open_price,
            "Status": "FILLED",
            "Reason": ""
        })

    else:
        raise RuntimeError(f"Order type not recognized for buys. ({order_type})")

    return portfolio_df, cash
