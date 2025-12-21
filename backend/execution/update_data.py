import pandas as pd 
import yfinance as yf
from datetime import date

#TODO: ticker range fails on weekends
def get_market_data(ticker):
        yesterdays_market_date = pd.Timestamp.now().date()
        todays_market_date = pd.Timestamp.now().date() + pd.Timedelta(days=1)
        ticker_data = yf.download(ticker, start=yesterdays_market_date, end=todays_market_date, auto_adjust=True)
        ticker_data.iloc[-1]
        return ticker_data

def update_market_value_column(portfolio):
    portfolio = portfolio.copy()

    for i, row in portfolio.iterrows():
        ticker = row["ticker"]
        shares = row["shares"]

        ticker_data = get_market_data(ticker)
        close_price = ticker_data["Close"]

        portfolio.at[i, "market_value"] = close_price * shares

    return portfolio
