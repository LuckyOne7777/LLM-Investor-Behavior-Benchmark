import yfinance as yf
import datetime
from pathlib import Path
import pandas as pd
def get_macro_news(n: int = 5):
    ticker = yf.Ticker("^GSPC")
    news_headlines = ticker.news
    titles = [item["content"].get("title") for item in news_headlines]
    return "\n".join(titles[:n])

def get_ticker_news(ticker_symbol: str, n: int = 3):
    ticker = yf.Ticker(ticker_symbol)
    news_headlines = ticker.news
    titles = [item["content"].get("title") for item in news_headlines]
    return "\n".join(titles[:n])

def recent_execution_logs(model_name: str, look_back: int = 5):
    TRADE_LOG_PATH = Path(f"models/{model_name}/trade_log.csv")
    TODAY = pd.Timestamp.now().date()
    time_range = TODAY - datetime.timedelta(days=look_back)
    trade_log = pd.read_csv(TRADE_LOG_PATH)
    trade_log["Date"] = pd.to_datetime(trade_log["Date"]).dt.date
    return trade_log[trade_log["Date"] >= time_range]

