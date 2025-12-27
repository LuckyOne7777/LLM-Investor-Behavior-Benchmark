import yfinance as yf
import datetime
from pathlib import Path
import pandas as pd
from backend.LIBB import LIBBmodel
from datetime import datetime, timedelta

def truncate(text: str, limit: int):
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "..."

def get_macro_news(n: int = 5, summary_limit: int = 200):
    ticker = yf.Ticker("^GSPC")
    news_headlines = ticker.news[:n]
    output = []
    for item in news_headlines:
        content = item.get("content", {})
        titles = content.get("title", "").strip()
        raw_summary = (
            content.get("summary")
            or item.get("summary")
            or ""  # Fallback if neither exists
        )
        summaries = truncate(raw_summary, summary_limit)
        output.append(f"{titles} - {summaries}")
    return "\n".join(output)

def get_ticker_news(ticker_symbol: str, n: int = 2, summary_limit: int = 150):
    ticker = yf.Ticker(ticker_symbol)
    news_headlines = ticker.news[:n]
    output = []
    for item in news_headlines:
        content = item.get("content", {})
        titles = content.get("title", "").strip()
        raw_summary = (
            content.get("summary")
            or item.get("summary")
            or ""  # Fallback if neither exists
        )
        summaries = truncate(raw_summary, summary_limit)
        output.append(f"{ticker_symbol} - {titles} - {summaries}")
    return "\n".join(output)

def get_portfolio_news(portfolio, n: int = 2, summary_limit: int = 150):
    tickers = portfolio["ticker"]
    if portfolio.empty:
        return ("Portfolio is empty.")
    portfolio_news = []
    for ticker in tickers:
        ticker_news = get_ticker_news(ticker, n, summary_limit)
        portfolio_news.append(f"{ticker_news}")
    return ("\n\n").join(portfolio_news)




def recent_execution_logs(trade_log_path: str, date: None | str | datetime = None, look_back: int = 5):
    if date is None:
        TODAY = pd.Timestamp.now().date()
    else:
        TODAY = pd.Timestamp(date).date() 
    time_range = TODAY - timedelta(days=look_back)
    trade_log = pd.read_csv(trade_log_path)
    trade_log["Date"] = pd.to_datetime(trade_log["Date"]).dt.date
    if trade_log[trade_log["Date"] >= time_range].empty:
        return f"No execution data for the past {look_back} days."
    else:
        return trade_log[trade_log["Date"] >= time_range]    