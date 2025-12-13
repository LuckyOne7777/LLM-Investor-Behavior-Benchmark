from pathlib import Path
from .portfolio import add_or_update_position
from .io import append_log

def process_buy(order, portfolio_df, cash, trade_log):
    ticker = order["ticker"].upper()
    shares = float(order["shares"])
    price = float(order["limit_price"])
    stop_loss = order["stop_loss"]

    cost = shares * price

    if cost > cash:
        append_log(trade_log, {
            "Date": order["date"],
            "Ticker": ticker,
            "Action": "BUY",
            "Shares": shares,
            "Price": price,
            "Status": "FAILED",
            "Reason": "Insufficient cash"
        })
        return portfolio_df, cash

    portfolio_df = add_or_update_position(
        portfolio_df, ticker, shares, price, stop_loss
    )
    cash -= cost

    append_log(trade_log, {
        "Date": order["date"],
        "Ticker": ticker,
        "Action": "BUY",
        "Shares": shares,
        "Price": price,
        "Status": "FILLED",
        "Reason": ""
    })

    return portfolio_df, cash
