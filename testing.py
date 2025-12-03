import yfinance as yf

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



