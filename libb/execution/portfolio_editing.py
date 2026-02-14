import pandas as pd
from typing import cast
from .utils import catch_missing_order_data
from pathlib import Path
from ..other.types_file import Order

def add_or_update_position(df: pd.DataFrame, ticker: str, shares: int, price: float, stop_loss: float) -> pd.DataFrame:
    cost = shares * price

    if ticker in df["ticker"].values:
        idx = df.index[df["ticker"] == ticker][0]
        old_shares = df.loc[idx, "shares"]
        if pd.isna(old_shares):
            raise TypeError(f"Old shares for {ticker} is missing.")
        old_shares = float(cast(float, old_shares))

        old_cost = df.loc[idx, "cost_basis"]
        old_cost = float(cast(float, old_cost))

        new_shares = old_shares + shares
        new_cost = old_cost + cost

        df.loc[idx, "shares"] = new_shares
        df.loc[idx, "cost_basis"] = new_cost
        df.loc[idx, "buy_price"] = new_cost / new_shares

    else:
        new_row = {
            "ticker": ticker,
            "shares": shares,
            "buy_price": price,
            "cost_basis": cost,
            "stop_loss": stop_loss,
        }
        if not df.empty:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

    return df

def reduce_position(df: pd.DataFrame, ticker: str, shares: int) -> tuple[pd.DataFrame, float]:
    idx = df.index[df["ticker"] == ticker][0]
    row = df.loc[idx]

    remaining = row["shares"] - shares
    buy_price = float(row["buy_price"])

    if remaining == 0:
        df = df.drop(idx).reset_index(drop=True)
    else:
        df.loc[idx, "shares"] = remaining
        df.loc[idx, "cost_basis"] = buy_price * remaining

    return df, buy_price



def update_stoploss(df: pd.DataFrame, order: Order, trade_log_path: Path) -> bool:
    required_cols = ["ticker", "stop_loss"]
    if not catch_missing_order_data(order, required_cols, trade_log_path):
        return False
    
    ticker = order["ticker"]
    stop_loss = order["stop_loss"]
    assert stop_loss is not None
        
    df.loc[df["ticker"] == ticker, "stop_loss"] = float(stop_loss)
    return True