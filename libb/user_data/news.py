import yfinance as yf

def truncate(text: str, limit: int):
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "..."

def _get_macro_news(n: int = 5, summary_limit: int = 200):
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

    As a result, this function is NOT suitable for:
      - historical macro analysis
      - backtesting
      - event-driven research
      - machine learning datasets
      - reproducible studies

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

def _get_ticker_news(ticker_symbol: str, n: int = 2, summary_limit: int = 150):
    """
    Fetch and format the most recent news headlines for a single stock ticker
    using yfinance.

    CRITICAL LIMITATION: 
    --------------------
    This function ONLY returns news available on the CURRENT DAY.
    Due to Yahoo Finance / yfinance backend limitations:
      - Historical news is NOT accessible
      - There is NO pagination
      - Increasing `n` does NOT retrieve older articles
      - Returned headlines may change or disappear over time

    This function should be treated as a "latest headlines snapshot"
    at the moment it is called.

    Parameters
    ----------
    ticker_symbol : str
        Stock ticker symbol (e.g., "AAPL", "MSFT").

    n : int, optional
        Maximum number of headlines to include from today's available news.
        Defaults to 2. Increasing this value does NOT extend history.

    summary_limit : int, optional
        Maximum number of characters to include in the truncated summary.
        Defaults to 150.

    Returns
    -------
    str
        A newline-separated string of formatted news items in the form:
        "<TICKER> - <TITLE> - <TRUNCATED SUMMARY>".

    Notes
    -----
    Internally relies on `yf.Ticker(ticker_symbol).news`, which returns
    a small, non-deterministic set of recent headlines with no date guarantees.
    """
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

def _get_portfolio_news(portfolio, n: int = 2, summary_limit: int = 150):
    tickers = portfolio["ticker"]
    if portfolio.empty:
        return ("Portfolio is empty.")
    portfolio_news = []
    for ticker in tickers:
        ticker_news = _get_ticker_news(ticker, n, summary_limit)
        portfolio_news.append(f"{ticker_news}")
    return ("\n\n").join(portfolio_news)