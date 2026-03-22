import matplotlib.pyplot as plt
from libb.execution.get_market_data import download_data_on_given_range
import pandas as pd

def download_baseline(portfolio_df: pd.DataFrame, ticker: str, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """Download prices and normalise baseline to starting capital."""

    starting_capital = portfolio_df["equity"].iloc[0]

    baseline = download_data_on_given_range(ticker, start_date, end_date)
    if baseline is None:
        raise RuntimeError(f"Data sources returned None while downloading baseline data (ticker: {ticker}). Check your internet or try again later.")    
    baseline_df = pd.DataFrame({"Close": baseline["Close"], "Date": baseline["Close"].index}).reset_index(drop=True)
    starting_price = baseline_df.loc[baseline_df.index[0], "Close"]

    scaling_factor = starting_capital / starting_price
    baseline_df["Adjusted Value"] = baseline_df["Close"] * scaling_factor
    return baseline_df[["Date", "Adjusted Value"]]

def plot_equity_vs_baseline(portfolio_path, baseline_ticker="^SPX") -> None:
    """Generate and display the comparison graph; return metrics."""
    portfolio_history = pd.read_csv(portfolio_path)
    portfolio_history["date"] = pd.to_datetime(portfolio_history["date"])

    start_date = portfolio_history["date"].iloc[0]
    end_date = portfolio_history["date"].iloc[-1]
    starting_equity = portfolio_history["equity"].iloc[0]
    baseline = download_baseline(portfolio_history, baseline_ticker, start_date, end_date)

    # plotting
    plt.figure(figsize=(10, 6))
    plt.style.use("seaborn-v0_8-whitegrid")

    plt.plot(
        portfolio_history["date"],
        portfolio_history["equity"],
        label=f"Portfolio (${starting_equity} Invested)",
        marker="o",
        color="blue",
        linewidth=2,
    )
    plt.plot(
        baseline["Date"],
        baseline["Adjusted Value"],
        label=f"{baseline_ticker} (${starting_equity} Invested)",
        marker="o",
        color="orange",
        linestyle="--",
        linewidth=2,
    )

    # annotate final P/Ls
    final_date = portfolio_history["date"].iloc[-1]
    final_portfolio_value = float(portfolio_history["equity"].iloc[-1])
    final_baseline_value = float(baseline["Adjusted Value"].iloc[-1])
    y_offset = (plt.ylim()[1] - plt.ylim()[0]) * 0.03

    portfolio_pct_return = (final_portfolio_value - starting_equity) / starting_equity * 100
    baseline_pct_return = (final_baseline_value - starting_equity) / starting_equity * 100

    plt.text(
    final_date,
    final_portfolio_value + y_offset,
    
    f"{portfolio_pct_return:.2f}%",
    color="blue",
            )

    plt.text(
    final_date,
    final_baseline_value + y_offset,
    f"{baseline_pct_return:.2f}%",
    color="orange",
            )

    plt.title(f"Portfolio vs. {baseline_ticker}")
    plt.xlabel("Date")
    plt.ylabel(f"Value of ${starting_equity} Investment")
    plt.xticks(rotation=15)
    plt.legend()
    plt.grid(True)

    plt.show()

def plot_equity(portfolio_path):
    """Generate and display the comparison graph; return metrics."""
    portfolio_history = pd.read_csv(portfolio_path)
    portfolio_history["date"] = pd.to_datetime(portfolio_history["date"])

    starting_equity = portfolio_history["equity"].iloc[0]

    # plotting
    plt.figure(figsize=(10, 6))
    plt.style.use("seaborn-v0_8-whitegrid")

    plt.plot(
        portfolio_history["date"],
        portfolio_history["equity"],
        label=f"Portfolio (${starting_equity} Invested)",
        marker="o",
        color="blue",
        linewidth=2,
    )

    # annotate final P/Ls
    final_date = portfolio_history["date"].iloc[-1]
    final_portfolio_value = float(portfolio_history["equity"].iloc[-1])
    y_offset = (plt.ylim()[1] - plt.ylim()[0]) * 0.03

    pct_return = (final_portfolio_value - starting_equity) / starting_equity * 100

    plt.text(
    final_date,
    final_portfolio_value + y_offset,
    f"{pct_return:.2f}%",
    color="blue",
            )

    plt.title(f"Portfolio Balance")
    plt.xlabel("Date")
    plt.ylabel(f"Value of ${starting_equity} Investment")
    plt.xticks(rotation=15)
    plt.legend()
    plt.grid(True)

    plt.show()