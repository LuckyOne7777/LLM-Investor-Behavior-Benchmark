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
    
    assert "date" in trade_df.columns and positions_df.columns and equity_df.columns

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
    """
    Computes average portfolio concentration based on Herfindahl-Hirschman Index (HHI).
    Input:
        df_positions: daily position values
        df_equity: total equity
    Output:
        float (0 to 1)
    """

    weights = df_positions.div(df_equity, axis=0)
    daily_hhi = (weights**2).sum(axis=1)
    return float(daily_hhi.mean())

def turnover_ratio(df_trades: pd.DataFrame, df_equity: pd.DataFrame) -> float:
    filled_trades = df_trades[df_trades["status"] == "FILLED"]
    total_trade_value = (filled_trades["price"] * filled_trades["shares"]).sum()
    avg_equity = df_equity["equity"].mean()
    return total_trade_value / avg_equity

def total_behavioral_metrics(trade_df_path: Path | str, positions_df_path: Path | str, portfolio_history_df_path: Path | str, date: str | date):

    trade_df, positions_df, equity_df = load_behavioral_metrics_data(trade_df_path, positions_df_path, portfolio_history_df_path)

    hhi_index = concentration_ratio(positions_df, equity_df)
    loss_aversion_score = loss_aversion(trade_df)
    turnover = turnover_ratio(trade_df, equity_df)

    average_cash_pct = round((equity_df["cash"].mean() / equity_df["equity"].mean()) * 100, 2)
    median_cash_pct = round((equity_df["cash"].median() / equity_df["equity"].median()) * 100, 2)

    average_positions = len(positions_df) / positions_df["date"].nunique()
    median_positions = round((positions_df.groupby("date").size().median()), 2)
    max_positions = positions_df.groupby("date").size().max()

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