import pandas as pd
from pathlib import Path
from typing import Any
from datetime import date

def load_behavioral_metrics_data(trade_df_path: Path | str, positions_df_path: Path | str, position_history_df_path: Path | str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trade_df = pd.read_csv(trade_df_path)
    positions_df = pd.read_csv(positions_df_path)
    equity_df = pd.read_csv(position_history_df_path)

    df_dict: dict = {"trade_df": trade_df,
            "positions_df": positions_df,
            "equity_df": equity_df}
    
    empty_dfs = [df_name for df_name, df_content in df_dict.items() if df_content.empty]

    if empty_dfs:
        raise RuntimeError(f"Cannot generate behavioral metrics: {", ".join(empty_dfs)}")
    
    assert "date" in trade_df.columns
    assert "date" in positions_df.columns 
    assert "date" in equity_df.columns

    return trade_df, positions_df, equity_df

def loss_aversion(trades_log: pd.DataFrame) -> None | float:
    """
    Computes loss aversion λ = avg loss magnitude / avg gain magnitude.
    Returns None if undefined.
    """
    if trades_log.empty or "PnL" not in trades_log.columns:
        return None

    losses = trades_log[trades_log["PnL"] < 0]["PnL"]
    gains = trades_log[trades_log["PnL"] > 0]["PnL"]

    if losses.empty or gains.empty:
        return None

    avg_loss = abs(losses.mean())
    avg_gain = gains.mean()

    if avg_gain == 0:
        return None

    return avg_loss / avg_gain


def concentration_ratio(df_positions: pd.DataFrame, df_equity: pd.DataFrame) -> float:
    wide_positions = df_positions.pivot_table(
        index="date", 
        columns="ticker", 
        values="market_value", 
        aggfunc="sum",
        fill_value=0
    )
    
    equity_series = df_equity.set_index("date")["equity"]
    equity_series = equity_series.reindex(wide_positions.index)

    positions_total = wide_positions.sum(axis=1)
    wide_positions["__cash__"] = equity_series - positions_total
    
    weights = wide_positions.div(equity_series, axis=0)
    daily_hhi = (weights**2).sum(axis=1)

    return float(daily_hhi.mean())

def turnover_ratio(df_trades: pd.DataFrame, df_equity: pd.DataFrame) -> float:
    filled_trades = df_trades[df_trades["status"] == "FILLED"]
    total_trade_value = (filled_trades["executed_price"] * filled_trades["shares"]).sum()
    avg_equity = df_equity["equity"].mean()
    return total_trade_value / avg_equity

def total_behavioral_metrics(trade_df_path: Path | str, positions_df_path: Path | str, portfolio_history_df_path: Path | str, date: str | date):
    """
    Compute all behavioral metrics from raw portfolio artifacts.

    Loads trade execution logs, position history, and portfolio equity
    history from disk and computes a fixed set of behavioral statistics
    describing LLM decision-making patterns over the full observation
    period.

    Args:
        trade_df_path (Path or str): Path to trade_log.csv.
            Required columns: date, action, status, PnL, executed_price, shares
        positions_df_path (Path or str): Path to position_history.csv.
            Required columns: date, ticker, market_value
        portfolio_history_df_path (Path or str): Path to portfolio_history.csv.
            Required columns: date, equity, cash
        date (str or date): The run date, recorded as metadata in the output.

    Returns:
        dict: A flat dictionary of behavioral metrics containing:
            - loss_aversion_score (float or None): Ratio of average loss
              magnitude to average gain magnitude across filled sells.
            - hhi_index (float): Average daily HHI across all observation
              days. Cash treated as explicit position. Range 0.0 to 1.0.
            - turnover_ratio (float): Total filled trade value divided by
              average portfolio equity.
            - avg_cash_pct (float): Mean daily cash as % of total equity.
            - med_cash_pct (float): Median daily cash as % of total equity.
            - avg_positions_per_day (float): Mean tickers held per day.
            - median_positions_per_day (float): Median tickers held per day.
            - max_positions_in_a_day (int): Peak concurrent positions.
            - total_buy_count (int): Buy orders across all statuses.
            - total_sell_count (int): Sell orders across all statuses.
            - total_failed_buys (int): Buy orders with status FAILED.
            - total_failed_sells (int): Sell orders with status FAILED.
            - total_rejected_buys (int): Buy orders with status REJECTED.
            - total_rejected_sells (int): Sell orders with status REJECTED.
            - start_date (str): First date in portfolio history.
            - end_date (str): Last date in portfolio history.
            - observation_count (int): Total trading days observed.
            - generated_at (str): Run date at time of generation.

    Raises:
        RuntimeError: If any of the three input DataFrames are empty.
    """

    trade_df, positions_df, equity_df = load_behavioral_metrics_data(trade_df_path, positions_df_path, portfolio_history_df_path)

    hhi_index = concentration_ratio(positions_df, equity_df)
    loss_aversion_score = loss_aversion(trade_df)
    turnover = turnover_ratio(trade_df, equity_df)

    average_cash_pct = round((equity_df["cash"].mean() / equity_df["equity"].mean()) * 100, 2)
    median_cash_pct = round((equity_df["cash"].median() / equity_df["equity"].median()) * 100, 2)

    average_positions = len(positions_df) / positions_df["date"].nunique()
    median_positions = round((positions_df.groupby("date").size().median()), 2)
    max_positions = int(positions_df.groupby("date").size().max())

    metrics_log = {
            "loss_aversion_score": loss_aversion_score,
            "hhi_index": float(hhi_index),
            "turnover_ratio": float(turnover),

            "avg_cash_pct": float(average_cash_pct),
            "med_cash_pct": float(median_cash_pct),

            "avg_positions_per_day": average_positions,
            "median_positions_per_day": median_positions,
            "max_positions_in_a_day": max_positions,

            "total_buy_count": int(len(trade_df[trade_df["action"] == "BUY"])),
            "total_sell_count": int(len(trade_df[trade_df["action"] == "SELL"])),
            "total_stoploss_updates": int(len(trade_df[trade_df["action"] == "UPDATE"])),
            "total_stoploss_sells": int(len(trade_df[trade_df["order_type"] == "STOPLOSS_MET"])),

            "total_failed_buys": int(len(trade_df[(trade_df["action"] == "BUY") & (trade_df["status"] == "FAILED")])),
            "total_failed_sells": int(len(trade_df[(trade_df["action"] == "SELL") & (trade_df["status"] == "FAILED")])),
            
            "total_rejected_buys": int(len(trade_df[(trade_df["action"] == "BUY") & (trade_df["status"] == "REJECTED")])),
            "total_rejected_sells": int(len(trade_df[(trade_df["action"] == "SELL") & (trade_df["status"] == "REJECTED")])),

            "start_date": str(equity_df["date"].iloc[0]),
            "end_date": str(equity_df["date"].iloc[-1]),
            "observation_count": len(equity_df),
            "generated_at": str(date),
        }
    return metrics_log

# ----------------------------------
# Possible Additional Metrics
# ----------------------------------

def risk_aversion(df_equity: pd.DataFrame, df_trades: pd.DataFrame) -> float:
    """
    Measures how often the model reduces risk after losses.
    Input:
        df_equity: DataFrame with daily equity
        df_trades: DataFrame with trades + position sizes
    Output:
        float (0 to 1)
    """
    # TODO: implement
    return 0.0

def momentum_factor(df_prices: pd.DataFrame, df_trades: pd.DataFrame, lookback: int=3) -> float:
    """
    Measures correlation between past k-day return and buy decisions.
    Input:
        df_prices: price history
        df_trades: trade log
    Output:
        float (-1 to 1)
    """
    # TODO: implement
    return 0.0

def volatility_tolerance(df_positions: pd.DataFrame, df_prices: pd.DataFrame) -> float:
    """
    Measures how willing the model is to hold volatile stocks.
    Input:
        df_positions: position sizes
        df_prices: volatility data
    Output:
        float
    """
    # TODO: implement
    return 0.0