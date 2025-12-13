from pathlib import Path
from .portfolio import reduce_position
from .io import append_log

def process_sell(order, portfolio_df, cash, trade_log):
    ticker = order["ticker"].upper()
    shares = float(order["shares"])
    price = float(order["limit_price"])

    if ticker not in portfolio_df["ticker"].values:
        append_log(trade_log, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "SELL",
            "Status": "FAILED",
            "Reason": "No position"
        })
        return portfolio_df, cash

    row = portfolio_df.loc[portfolio_df["ticker"] == ticker].iloc[0]
    if shares > row["shares"]:
        append_log(trade_log, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "SELL",
            "Status": "FAILED",
            "Reason": "Insufficient shares"
        })
        return portfolio_df, cash

    proceeds = shares * price
    portfolio_df, buy_price = reduce_position(portfolio_df, ticker, shares)
    cash += proceeds

    pnl = proceeds - (buy_price * shares)

    append_log(trade_log, {
        "Date": order["date"],
        "Ticker": ticker,
        "Action": "SELL",
        "Shares": shares,
        "Price": price,
        "PnL": pnl,
        "Status": "FILLED",
        "Reason": ""
    })

    return portfolio_df, cash
