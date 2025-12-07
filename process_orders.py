import pandas as pd
import json
import os
from typing import Tuple
from typing import TypedDict, Literal, List, Optional

TRADE_LOG = "trade_log.csv"
PENDING_LOG = "pending_orders.csv"

class Order(TypedDict):
    action: Literal["buy", "sell", "u"]     # "u" = update stop-loss
    ticker: str
    shares: int
    order_type: Literal["limit", "market", "update"]
    limit_price: Optional[float]
    time_in_force: Optional[str]
    date: str                               # YYYY-MM-DD
    stop_loss: Optional[float]
    rationale: str
    confidence: float                       # 0–1


def load_df(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


def append_log(path: str, row: dict):
    df = load_df(path)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)


def process_logic(
    portfolio_df: pd.DataFrame,
    cash: float,
    order: Order
) -> Tuple[pd.DataFrame, float]:
    """Process orders, update portfolio and output results to 'trade_log.csv'. """
    action = order["action"]
    ticker = order["ticker"].upper()
    shares = float(order["shares"])
    limit_price = None if order["limit_price"] in (None, "NA") else float(order["limit_price"])
    stop_loss = order["stop_loss"]
    rationale = order["rationale"]
    today = order["date"]
    confidence = float(order["confidence"])

    # ---------------------------------------
    # STOP-LOSS UPDATE
    # ---------------------------------------
    if action == "u":
        if ticker not in portfolio_df["ticker"].values:
            append_log(TRADE_LOG, {
                "Date": today,
                "Ticker": ticker,
                "Action": "UPDATE_STOPLOSS",
                "Shares": 0,
                "Price": "",
                "Cost Basis": "",
                "PnL": "",
                "Rationale": rationale,
                "Confidence": confidence,
                "Status": "FAILED",
                "Reason": f"{ticker} not in portfolio"
            })
            return portfolio_df, cash

        # update stop
        portfolio_df.loc[portfolio_df["ticker"] == ticker, "stop_loss"] = float(stop_loss)

        append_log(TRADE_LOG, {
            "Date": today,
            "Ticker": ticker,
            "Action": "UPDATE_STOPLOSS",
            "Shares": 0,
            "Price": "",
            "Cost Basis": "",
            "PnL": "",
            "Rationale": rationale,
            "Confidence": confidence,
            "Status": "FILLED",
            "Reason": ""
        })

        return portfolio_df, cash

    # ---------------------------------------
    # BUY ORDER
    # ---------------------------------------
    if action == "buy":
        if limit_price is None:
            raise ValueError("Buy order missing limit price.")

        cost = shares * limit_price

        # Rejection — insufficient cash
        if cost > cash:
            append_log(TRADE_LOG, {
                "Date": today,
                "Ticker": ticker,
                "Action": "BUY",
                "Shares": shares,
                "Price": limit_price,
                "Cost Basis": "",
                "PnL": "",
                "Rationale": rationale,
                "Confidence": confidence,
                "Status": "FAILED",
                "Reason": "Insufficient cash"
            })
            return portfolio_df, cash

        # SUCCESS — update portfolio
        if ticker in portfolio_df["ticker"].values:
            idx = portfolio_df.index[portfolio_df["ticker"] == ticker][0]
            old_shares = float(portfolio_df.loc[idx, "shares"])
            old_cost = float(portfolio_df.loc[idx, "cost_basis"])

            portfolio_df.loc[idx, "shares"] = old_shares + shares
            portfolio_df.loc[idx, "cost_basis"] = old_cost + cost

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
            "Price": limit_price,
            "Cost Basis": cost,
            "PnL": "",
            "Rationale": rationale,
            "Confidence": confidence,
            "Status": "FILLED",
            "Reason": ""
        })

        return portfolio_df, cash

    # ---------------------------------------
    # SELL ORDER
    # ---------------------------------------
    if action == "sell":
        if ticker not in portfolio_df["ticker"].values:
            append_log(TRADE_LOG, {
                "Date": today,
                "Ticker": ticker,
                "Action": "SELL",
                "Shares": shares,
                "Price": limit_price,
                "Cost Basis": "",
                "PnL": "",
                "Rationale": rationale,
                "Confidence": confidence,
                "Status": "FAILED",
                "Reason": "No position"
            })
            return portfolio_df, cash

        idx = portfolio_df.index[portfolio_df["ticker"] == ticker][0]
        row = portfolio_df.loc[idx]

        if shares > row["shares"]:
            append_log(TRADE_LOG, {
                "Date": today,
                "Ticker": ticker,
                "Action": "SELL",
                "Shares": shares,
                "Price": limit_price,
                "Cost Basis": "",
                "PnL": "",
                "Rationale": rationale,
                "Confidence": confidence,
                "Status": "FAILED",
                "Reason": "Insufficient shares"
            })
            return portfolio_df, cash

        proceeds = shares * limit_price
        buy_price = float(row.get("buy_price", limit_price))
        cost_basis_used = buy_price * shares
        pnl = proceeds - cost_basis_used

        # update shares
        remaining = row["shares"] - shares
        if remaining == 0:
            portfolio_df = portfolio_df.drop(idx).reset_index(drop=True)
        else:
            portfolio_df.loc[idx, "shares"] = remaining
            portfolio_df.loc[idx, "cost_basis"] = buy_price * remaining

        cash += proceeds

        append_log(TRADE_LOG, {
            "Date": today,
            "Ticker": ticker,
            "Action": "SELL",
            "Shares": shares,
            "Price": limit_price,
            "Cost Basis": cost_basis_used,
            "PnL": pnl,
            "Rationale": rationale,
            "Confidence": confidence,
            "Status": "FILLED",
            "Reason": ""
        })

        return portfolio_df, cash

    # ---------------------------------------
    # Unknown
    # ---------------------------------------
    raise ValueError(f"Unknown action: {action}")
