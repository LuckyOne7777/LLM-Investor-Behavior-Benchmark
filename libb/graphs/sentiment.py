import pandas as pd
import matplotlib.pyplot as plt
import json


def plot_equity_and_sentiment(
    portfolio_csv: str,
    sentiment_json: str,
):
    """
    Creates a two-panel plot:
    - Top: Portfolio equity over time
    - Bottom: Sentiment polarity over time

    Portfolio timeline is authoritative.
    Sentiment is left-joined by date.
    """
    plt.close("all")
    # --- Load portfolio CSV ---
    portfolio = pd.read_csv(portfolio_csv)
    portfolio["date"] = pd.to_datetime(portfolio["date"])
    

    # --- Load sentiment JSON ---
    with open(sentiment_json, "r") as f:
        sentiment_records = json.load(f)

    sentiment = pd.DataFrame(sentiment_records)
    sentiment["date"] = pd.to_datetime(sentiment["date"])
    sentiment = sentiment[["date", "polarity"]]

    # --- Merge on date ---
    df = (
        portfolio
        .merge(sentiment, on="date", how="left")
        .sort_values("date")
    )
    df = df.dropna(subset=["polarity"])


    # ======================
    # Create subplots
    # ======================
    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        sharex=True,
        figsize=(10, 6)
    )

    # --- Top plot: Equity ---
    ax1.plot(df["date"], df["equity"])
    ax1.set_title("Portfolio Equity Over Time")
    ax1.set_ylabel("Equity")
    ax1.grid(True)

    # --- Bottom plot: Sentiment ---
    ax2.plot(df["date"], df["polarity"])
    ax2.axhline(0, linestyle="--")
    ax2.set_title("Sentiment Polarity Over Time")
    ax2.set_ylabel("Polarity")
    ax2.set_xlabel("Date")
    ax2.grid(True)

    plt.tight_layout()
    plt.show()
