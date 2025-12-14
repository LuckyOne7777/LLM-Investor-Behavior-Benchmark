import yfinance as yf
import datetime
from pathlib import Path
import pandas as pd
from execution.LIBB import LIBBmodel
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

def get_ticker_news(ticker_symbol: str, n: int = 3, summary_limit: int = 150):
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
        output.append(f"{titles} - {summaries}")
    return "\n".join(output)


def recent_execution_logs(trade_log_path: str, look_back: int = 5):
    TODAY = pd.Timestamp.now().date()
    time_range = TODAY - datetime.timedelta(days=look_back)
    trade_log = pd.read_csv(trade_log_path)
    trade_log["Date"] = pd.to_datetime(trade_log["Date"]).dt.date
    if trade_log[trade_log["Date"] >= time_range].empty == False:
        return trade_log[trade_log["Date"] >= time_range]
    else: return f"No execution data for the past {look_back} days."

l = LIBBmodel("models/gpt-5")
x = recent_execution_logs(l.trade_log_path)
print(x)


