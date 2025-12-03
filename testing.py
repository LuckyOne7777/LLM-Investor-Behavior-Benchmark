import yfinance as yf

def get_macro_news():
    ticker = yf.Ticker("^GSPC")
    news_headlines = ticker.news
    return news_headlines
news = get_macro_news()
print(news)
