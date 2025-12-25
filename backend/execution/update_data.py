import pandas as pd 
import yfinance as yf
from typing import TypedDict

#TODO: ticker range fails on weekends
#TODO: graceful error handling for ticker downloading
#TODO: Add additional data sources

class MarketDataObject(TypedDict):
     Low: float
     High: float
     Close: float
     Open: float
     Volume: int
     Ticker: str

def get_market_data(ticker: str) -> MarketDataObject:
        yesterdays_market_date = pd.Timestamp.now().date()
        todays_market_date = pd.Timestamp.now().date() + pd.Timedelta(days=1)
        try:
            ticker_data = yf.download(ticker, start=yesterdays_market_date, end=todays_market_date, auto_adjust=True, progress=False)
            if ticker_data is None:
                raise RuntimeError(f"YahooFinance API returned None for {ticker}. Try running again.")
        except Exception as e:
             raise RuntimeError(f"Error downloading {ticker}'s data: {e}. Try running again.")
        if isinstance(ticker_data.columns, pd.MultiIndex):
             ticker_data.columns = ticker_data.columns.get_level_values(0)
        data: MarketDataObject = {
            "Low": float(ticker_data["Low"].iloc[0]),
            "High": float(ticker_data["High"].iloc[0]),
            "Close": float(ticker_data["Close"].iloc[0]),
            "Open": float(ticker_data["Open"].iloc[0]),
            "Volume": int(ticker_data["Volume"].iloc[0]),
            "Ticker": str(ticker)
        }
        return data

def update_market_value_column(portfolio: pd.DataFrame) -> pd.DataFrame:
    portfolio = portfolio.copy()

    for i, row in portfolio.iterrows():
        ticker = row["ticker"]
        shares = row["shares"]

        ticker_data = get_market_data(ticker)
        close_price = ticker_data["Close"]
        portfolio.at[i, "market_price"] = close_price
        portfolio.at[i, "market_value"] = close_price * shares

    return portfolio
