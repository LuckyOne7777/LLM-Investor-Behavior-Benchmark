import pandas as pd 
import yfinance as yf
from ..other.types_file import MarketDataObject
from libb.execution.get_market_data import download_data_on_given_date
from datetime import date

#TODO: ticker range fails on weekends
#TODO: graceful error handling for ticker downloading
#TODO: Add additional data sources

def get_market_data(ticker: str, date: str | date) -> MarketDataObject:
        

    yesterdays_market_date = pd.Timestamp(date).date()

    todays_market_date = yesterdays_market_date + pd.Timedelta(days=1)

    # account for YF ticker differences
    ticker = ticker.replace(".", "-")
    try:
        ticker_data = yf.download(
        ticker,
        start=yesterdays_market_date,
        end=todays_market_date,
        auto_adjust=True,
        progress=False,
    )
    except Exception as e:
        raise RuntimeError(
            f"Failed to download market data for {ticker}"
        ) from e

    if ticker_data is None or ticker_data.empty:
        raise ValueError(
            f"No market data available for {ticker} on {yesterdays_market_date}. "
            "Market may have been closed (weekend or holiday)."
    )

    if isinstance(ticker_data.columns, pd.MultiIndex):
             ticker_data.columns = ticker_data.columns.get_level_values(0)
    data: MarketDataObject = {
            "Low": round(float(ticker_data["Low"].iloc[0]), 2),
            "High": round(float(ticker_data["High"].iloc[0]), 2),
            "Close": round(float(ticker_data["Close"].iloc[0]), 2),
            "Open": round(float(ticker_data["Open"].iloc[0]), 2),
            "Volume": int(ticker_data["Volume"].iloc[0]),
            "Ticker": str(ticker)
        }
    if data["Close"] is None:
         raise RuntimeError(f"{ticker} data for 'Close' is None")
    return data

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
