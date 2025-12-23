import pandas as pd

def add_or_update_position(df, ticker, shares, price, stop_loss):
    cost = shares * price

    if ticker in df["ticker"].values:
        idx = df.index[df["ticker"] == ticker][0]

        old_shares = float(df.loc[idx, "shares"])
        old_cost = float(df.loc[idx, "cost_basis"])

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
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    return df

def reduce_position(df, ticker, shares):
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

def update_stoploss(df, ticker, stop_loss) -> bool:
    if ticker not in df["ticker"].values:
        return False

    df.loc[df["ticker"] == ticker, "stop_loss"] = float(stop_loss)
    return True
