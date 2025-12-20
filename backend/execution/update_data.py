import pandas as pd 
import yfinance as yf
from datetime import date

def get_market_data(ticker):
        yesterdays_market_date = pd.Timestamp.now().date()
        todays_market_date = pd.Timestamp.now().date() + pd.Timedelta(days=1)
        # for stock in self.portfolio["ticker"]:
        ticker_data = yf.download(ticker, start=yesterdays_market_date, end=todays_market_date, auto_adjust=True, )
        return ticker_data