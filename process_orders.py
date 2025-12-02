import pandas as pd
import json
import os
from typing import Tuple
from datetime import date
from typing import TypedDict, Literal, List, Optional
TRADE_LOG = "trade_log.csv"
PENDING_LOG = "pending_orders.csv"

class Order(TypedDict):
    action: Literal["buy", "sell", "u"]            # "u" = update stop-loss
    ticker: str
    shares: int                                    # required for buy/sell, ignored for update
    order_type: Literal["limit", "market", "update"]
    limit_price: Optional[float]                   # None or numeric; always None for "market" and "update"
    time_in_force: Optional[str]                   # "DAY" or None for stop-loss update
    date: str                                      # YYYY-MM-DD
    stop_loss: Optional[float]                     # required for buy or stoploss update, None for sell
    rationale: str
    confidence: float                              # 0–1
def load_df(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


def append_log(path: str, row: dict):
    df = load_df(path)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)


def process_ai_order(
    portfolio_df: pd.DataFrame,
    cash: float,
    order: dict
) -> Tuple[pd.DataFrame, float]:

    action = order["action"]
    ticker = order["ticker"].upper()
    shares = float(order["shares"])
    limit_price = float(order["limit_price"]) if order["limit_price"] not in (None, "NA") else None
    stop_loss = float(order["stop_loss"])
    rationale = order["rationale"]
    today = order["date"]
    confidence = order["confidence"]

    # -------------------------------
    # UPDATE STOP LOSS
    # -------------------------------
    if action == "u":
        if ticker not in portfolio_df["ticker"].values:
            append_log(TRADE_LOG, {
                "Date": today,
                "Ticker": ticker,
                "Action": "UPDATE FAILED",
                "Reason": f"Stop-loss update failed: {ticker} not in portfolio",
                "Rationale": rationale
            })
            return portfolio_df, cash

        portfolio_df.loc[portfolio_df["ticker"] == ticker, "stop_loss"] = float(stop_loss)

        append_log(TRADE_LOG, {
            "Date": today,
            "Ticker": ticker,
            "Action": "UPDATE STOPLOSS",
            "New Stop Loss": stop_loss,
            "Rationale": rationale
        })

        return portfolio_df, cash

    # -------------------------------
    # BUY ORDER
    # -------------------------------
    if action == "b":


        cost = shares * limit_price
        if cost > cash:
            append_log(TRADE_LOG, {
                "Date": today,
                "Ticker": ticker,
                "Action": "BUY FAILED",
                "Reason": "Insufficient cash",
                "Rationale": rationale
            })
            return portfolio_df, cash

        # Success — update portfolio
        if ticker in portfolio_df["ticker"].values:
            idx = portfolio_df.index[portfolio_df["ticker"] == ticker][0]
            portfolio_df.loc[idx, "shares"] += shares
            portfolio_df.loc[idx, "cost_basis"] += cost
        else:
            new_row = {
                "ticker": ticker,
                "shares": shares,
                "buy_price": limit_price,
                "cost_basis": cost,
                "stop_loss": stop_loss
            }
            portfolio_df = pd.concat([portfolio_df, pd.DataFrame([new_row])], ignore_index=True)

        cash -= cost

        append_log(TRADE_LOG, {
            "Date": today,
            "Ticker": ticker,
            "Action": "BUY",
            "Shares": shares,
            "Exec Price": limit_price,
            "Cost": cost,
            "Rationale": rationale
        })

        return portfolio_df, cash

    # -------------------------------
    # SELL ORDER
    # -------------------------------
    if action == "s":
        if ticker not in portfolio_df["ticker"].values:
            append_log(TRADE_LOG, {
                "Date": today,
                "Ticker": ticker,
                "Action": "SELL FAILED",
                "Reason": "No position",
                "Rationale": rationale
            })
            return portfolio_df, cash

        idx = portfolio_df.index[portfolio_df["ticker"] == ticker][0]
        cur = portfolio_df.loc[idx]

        if shares > cur["shares"]:
            append_log(TRADE_LOG, {
                "Date": today,
                "Ticker": ticker,
                "Action": "SELL FAILED",
                "Reason": "Insufficient shares",
                "Rationale": rationale
            })
            return portfolio_df, cash

        proceeds = shares * limit_price

        # Update position
        new_shares = cur["shares"] - shares
        if new_shares == 0:
            portfolio_df = portfolio_df.drop(idx).reset_index(drop=True)
        else:
            portfolio_df.loc[idx, "shares"] = new_shares
            portfolio_df.loc[idx, "cost_basis"] = cur["cost_basis"] * (new_shares / cur["shares"])

        cash += proceeds

        append_log(TRADE_LOG, {
            "Date": today,
            "Ticker": ticker,
            "Action": "SELL",
            "Exec Price": limit_price,
            "Shares Sold": shares,
            "Proceeds": proceeds,
            "Rationale": rationale
        })

        return portfolio_df, cash

    raise ValueError(f"Unknown action: {action}")
