import pandas as pd
from typing import cast

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



def update_stoploss(df: pd.DataFrame, ticker: str, stop_loss: float) -> bool:
    if ticker not in df["ticker"].values:
        return False
    else:
        df.loc[df["ticker"] == ticker, "stop_loss"] = float(stop_loss)
        return True