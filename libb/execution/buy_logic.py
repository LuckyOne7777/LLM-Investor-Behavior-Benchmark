from .portfolio_editing import add_or_update_position
from .utils import append_log, catch_missing_order_data
from .update_data import get_market_data
import pandas as pd
from ..other.types_file import Order, TradeStatus
from pathlib import Path

def process_buy(order: Order, portfolio_df: pd.DataFrame, cash: float, trade_log_path: Path) -> tuple[pd.DataFrame, float, TradeStatus]:
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
        # return portfolio if null order
        if not catch_missing_order_data(order, required_cols, trade_log_path):
            return portfolio_df, cash, TradeStatus.FAILED

        
        assert intended_limit_price is not None
        intended_limit_price = float(intended_limit_price)
        # limit buy fails if price never trades at or below limit
        if market_low > intended_limit_price:
            append_log(trade_log_path, {
                "date": order["date"],
                "ticker": ticker,
                "action": "BUY",
                "status": "FAILED",
                "reason": f"limit price of {intended_limit_price} not met. (Low: {market_low})"
            })
            return portfolio_df, cash, TradeStatus.FAILED

        # realistic fill price
        fill_price = market_open if market_open <= intended_limit_price else intended_limit_price
        cost = shares * fill_price

        if cost > cash:
            append_log(trade_log_path, {
                "date": order["date"],
                "ticker": ticker,
                "action": "BUY",
                "status": "FAILED",
                "reason": "Insufficient cash"
            })
            return portfolio_df, cash, TradeStatus.FAILED

        portfolio_df = add_or_update_position(
            portfolio_df, ticker, shares, fill_price, stop_loss
        )
        cash -= cost

        append_log(trade_log_path, {
            "date": order["date"],
            "ticker": ticker,
            "action": "BUY",
            "shares": shares,
            "price": fill_price,
            "status": "FILLED",
            "reason": ""
        })

        return portfolio_df, cash, TradeStatus.FILLED

    # ---------- MARKET BUY ----------
    elif order_type == "market":

        required_cols = [
            "shares",
            "ticker",
        ]
        # return portfolio if null order
        if not catch_missing_order_data(order, required_cols, trade_log_path):
            return portfolio_df, cash, TradeStatus.FAILED
        cost = shares * market_open

        if cost > cash:
            append_log(trade_log_path, {
                "date": order["date"],
                "ticker": ticker,
                "action": "BUY",
                "status": "FAILED",
                "reason": "Insufficient cash"
            })
            return portfolio_df, cash, TradeStatus.FAILED


        append_log(trade_log_path, {
            "date": order["date"],
            "ticker": ticker,
            "action": "BUY",
            "shares": shares,
            "price": market_open,
            "status": "FILLED",
            "reason": ""
        })

        portfolio_df = add_or_update_position(
            portfolio_df, ticker, shares, market_open, stop_loss
        )

        cash -= cost

        return portfolio_df, cash, TradeStatus.FILLED



    else:
        append_log(trade_log_path, {
            "date": order["date"],
            "ticker": ticker,
            "action": "BUY",
            "shares": shares,
            "price": intended_limit_price,
            "status": "FAILED",
            "reason": f"ORDER TYPE UNKNOWN: {order_type}"
        })

        return portfolio_df, cash, TradeStatus.FAILED
