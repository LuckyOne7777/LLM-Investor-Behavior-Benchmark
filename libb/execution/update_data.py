import pandas as pd 
from libb.execution.get_market_data import download_data_on_given_date
from datetime import date

def update_market_value_columns(portfolio: pd.DataFrame, date: str | date) -> pd.DataFrame:
    portfolio = portfolio.copy()

    for i, row in portfolio.iterrows():
        ticker = row["ticker"]
        shares = row["shares"]
        cost_basis = portfolio.at[i, "cost_basis"]

        ticker_data = download_data_on_given_date(ticker, date)
        close_price = ticker_data["Close"]

        portfolio.at[i, "market_price"] = close_price
        portfolio.at[i, "market_value"] = round(close_price * shares, 2)
        portfolio.at[i, "unrealized_pnl"] = round(portfolio.at[i, "market_value"] - cost_basis, 2)

    return portfolio
