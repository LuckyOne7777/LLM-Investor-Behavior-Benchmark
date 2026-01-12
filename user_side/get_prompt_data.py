import yfinance as yf
import pandas as pd
from datetime import date, timedelta

def truncate(text: str, limit: int):
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "..."

def get_macro_news(n: int = 5, summary_limit: int = 200):
    """
    Fetch and format broad market (macro) news using yfinance.

      CRITICAL LIMITATION 
    -------------------------
    This function ONLY returns news available on the CURRENT DAY.
    It relies on `yf.Ticker("^GSPC").news`, which is subject to Yahoo Finance
    backend limitations:
      - No access to historical macro news
      - No pagination or date filtering
      - Increasing `n` does NOT retrieve older articles
      - Headline availability is non-deterministic and may change over time

    Treat the output strictly as a real-time snapshot of market headlines.

    Parameters
    ----------
    n : int, optional
        Maximum number of macro news headlines to include from today's
        available set. Defaults to 5.

    summary_limit : int, optional
        Maximum number of characters to include in the truncated summary.
        Defaults to 200.

    Returns
    -------
    str
        A newline-separated string of formatted macro news items in the form:
        "<TITLE> - <TRUNCATED SUMMARY>".

    Notes
    -----
    Uses the S&P 500 index ("^GSPC") as a proxy for general market news.
    Yahoo Finance may return fewer items than requested or none at all.
    """
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