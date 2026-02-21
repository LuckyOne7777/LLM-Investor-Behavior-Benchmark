import yfinance as yf
from libb.other.types_file import MarketConfig, MarketDataObject, MarketHistoryObject
from datetime import date
import pandas as pd
import io
import requests
from typing import cast, Tuple

#TODO: Set properly set up config

def get_valid_data_sources() -> Tuple[list[str], MarketConfig]:
    config = MarketConfig.from_env()

    valid_data_sources = ["yf", "stooq"]

    if config.finnhub_key is not None:
        valid_data_sources.append("finnhub")
    if config.alpha_vantage_key is not None:
        valid_data_sources.append("alpha_vantage")
    return valid_data_sources, config

def download_data_on_given_date(ticker: str, date: date | str) -> MarketDataObject:
    start_date = pd.Timestamp(date)
    end_date = start_date + pd.Timedelta(days=1)

    data = download_data_on_given_range(ticker, start_date, end_date)
    try:
        snapshot: MarketDataObject = {
            "Ticker": ticker,
            "Low": float(data["Low"].iloc[0]),
            "High": float(data["High"].iloc[0]),
            "Close": float(data["Close"].iloc[0]),
            "Open": float(data["Open"].iloc[0]),
            "Volume": int(data["Volume"].iloc[0]),
                                    }
    except Exception as e:
        raise TypeError(f"Could not convert MarketHistoryObject to MarketDataObject: ({e})")
    
    return snapshot

def download_data_on_given_range(ticker: str, start_date: date | str, end_date: date | str) -> MarketHistoryObject:
    valid_data_sources, config = get_valid_data_sources()
    for source in valid_data_sources:
        match source:

            case "yf":
                try:
                    data = download_yf_data(ticker, start_date, end_date)
                    if data is not None:
                            return cast(MarketHistoryObject, data)
                except Exception as e:
                    print(f"Failed download from yf: {e}")

            case "stooq":
                try:
                    data = download_stooq_data(ticker, start_date, end_date)
                    if data is not None:
                        return cast(MarketHistoryObject, data)
                except Exception as e:
                    print(f"Failed download from stooq: {e}")

    raise RuntimeError(f"""All valid data sources ({valid_data_sources}) failed to return valid data. 
                       Try setting more valid API keys in your environment or checking your internet.""")


def download_yf_data(ticker: str, start_date: date | str, end_date: date | str) -> MarketHistoryObject:

    # account for YF ticker differences
    ticker = ticker.replace(".", "-")

    try:
        ticker_data = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False,
    )
    except Exception as e:
        raise RuntimeError(
            f"Failed to download market data for {ticker}"
        ) from e

    if ticker_data is None or ticker_data.empty:
        raise ValueError(
            f"No market data available for {ticker}. "
            "Market may have been closed (weekend or holiday)."
    )

    if isinstance(ticker_data.columns, pd.MultiIndex):
             ticker_data.columns = ticker_data.columns.get_level_values(0)
    data: MarketHistoryObject = {
            "Low": round(ticker_data["Low"], 2),
            "High": round(ticker_data["High"], 2),
            "Close": round(ticker_data["Close"], 2),
            "Open": round(ticker_data["Open"], 2),
            "Volume": ticker_data["Volume"],
            "Ticker": str(ticker),
            "start_date": str(start_date),
            "end_date": str(end_date)
        }
    return data

def download_finnhub_data(ticker: str, start_date: date | str, end_date: date | str, config: MarketConfig) -> MarketHistoryObject:
    # Convert dates to Unix timestamps (seconds)
    to_unix = lambda d: int(pd.Timestamp(d).timestamp())
    
    params = {
        "symbol": ticker.upper(),
        "resolution": "D",
        "from": to_unix(start_date),
        "to": to_unix(end_date),
        "token": config.finnhub_key
    }

    try:
        response = requests.get("https://finnhub.io/api/v1/stock/candle", params=params)
        response.raise_for_status()
        res_data = response.json()
    except Exception as e:
        raise RuntimeError(f"Finnhub request failed for {ticker}") from e

    # Finnhub returns 's': 'ok' if successful
    if res_data.get("s") != "ok":
        raise ValueError(f"No Finnhub data for {ticker}. API message: {res_data.get('s')}")

    # Convert lists to Series with a DatetimeIndex
    dates = pd.to_datetime(res_data["t"], unit="s")
    
    data: MarketHistoryObject = {
        "Low": pd.Series(res_data["l"], index=dates).round(2),
        "High": pd.Series(res_data["h"], index=dates).round(2),
        "Close": pd.Series(res_data["c"], index=dates).round(2),
        "Open": pd.Series(res_data["o"], index=dates).round(2),
        "Volume": pd.Series(res_data["v"], index=dates).astype(int),
        "Ticker": ticker,
        "start_date": str(start_date),
        "end_date": str(end_date)
    }
    return data

def download_alpha_vantage_data(ticker: str, start_date: date | str, end_date: date | str, config: MarketConfig) -> MarketHistoryObject | None:
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker.upper(),
        "outputsize": "full", # 'full' to ensure we get older history
        "apikey": config.alpha_vantage_key
    }

    try:
        response = requests.get("https://www.alphavantage.co/query", params=params)
        res_data = response.json()
        
        # Alpha Vantage returns errors in a 'Note' or 'Error Message' field
        if "Error Message" in res_data or "Note" in res_data:
            raise ValueError(res_data.get("Error Message") or res_data.get("Note"))

        # The actual data is under this key
        raw_series = res_data["Time Series (Daily)"]
    except Exception as e:
        raise RuntimeError(f"Alpha Vantage failed for {ticker}") from e

    # Convert to DataFrame to handle slicing by date easily
    df = pd.DataFrame.from_dict(raw_series, orient="index").astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    # Slice the range
    mask = (df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))
    ticker_data = df.loc[mask]

    if ticker_data.empty:
        raise ValueError(f"Alpha Vantage range empty for {ticker}")

    data: MarketHistoryObject = {
        "Low": ticker_data["3. low"].round(2),
        "High": ticker_data["2. high"].round(2),
        "Close": ticker_data["4. close"].round(2),
        "Open": ticker_data["1. open"].round(2),
        "Volume": ticker_data["5. volume"].astype(int),
        "Ticker": ticker,
        "start_date": str(start_date),
        "end_date": str(end_date)
    }
    return data

def download_stooq_data(
    ticker: str,
    start_date: date | str,
    end_date: date | str,
) -> MarketHistoryObject:
    """
    Download daily historical data from Stooq.
    Stooq does not require an API key.

    Notes:
    - Dates must be formatted as YYYYMMDD
    - Stooq expects lowercase tickers
    - US tickers usually work as-is (e.g. AAPL)
    - Some exchanges require suffixes (e.g. .us, .pl)
    """

    ticker = ticker.lower()

    # If no exchange suffix, assume US
    if "." not in ticker:
        ticker_stooq = f"{ticker}.us"

    # Convert dates to YYYYMMDD format
    start_str = pd.Timestamp(start_date).strftime("%Y%m%d")
    end_str = pd.Timestamp(end_date).strftime("%Y%m%d")

    url = "https://stooq.com/q/d/l/"
    params = {
        "s": ticker_stooq,
        "i": "d",  # daily interval
        "d1": start_str,
        "d2": end_str,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Stooq request failed for {ticker}") from e

    if not response.text.strip():
        raise ValueError(f"No Stooq data returned for {ticker}")

    try:
        df = pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        raise RuntimeError(f"Failed to parse Stooq CSV for {ticker}") from e

    if df.empty:
        raise ValueError(f"Empty Stooq dataset for {ticker}")

    # Stooq returns columns:
    # Date,Open,High,Low,Close,Volume
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")

    data: MarketHistoryObject = {
        "Low": df["Low"].round(2),
        "High": df["High"].round(2),
        "Close": df["Close"].round(2),
        "Open": df["Open"].round(2),
        "Volume": df["Volume"].fillna(0).astype(int),
        "Ticker": ticker,
        "start_date": str(start_date),
        "end_date": str(end_date),
    }

    return data
