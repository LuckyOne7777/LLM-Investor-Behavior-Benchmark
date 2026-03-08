import numpy as np
import pandas as pd
import json
from datetime import date
from pathlib import Path
import yfinance as yf

def load_performance_data(portfolio_history_path: Path | str, trade_log_path: Path | str, baseline_ticker: str) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    raw_portfolio_log = pd.read_csv(portfolio_history_path, parse_dates=["date"])
    raw_trade_log = pd.read_csv(trade_log_path)
    raw_portfolio_log = raw_portfolio_log.set_index("date")

    assert raw_portfolio_log.index.is_unique, "Duplicate processed dates within portfolio log."

    if raw_portfolio_log.empty:
        raise RuntimeError("Cannot generate performance metrics: `portfolio_history.csv` is empty.")
    
    first_date = raw_portfolio_log.index[0]
    last_date = raw_portfolio_log.index[-1]

    baseline_data = yf.download(baseline_ticker, start=first_date, end=last_date + pd.Timedelta(days=1), auto_adjust=True, progress=False)
    if baseline_data is None:
        raise RuntimeError(f"Cannot generate performance metrics: ticker data {baseline_ticker} was type None.")

    baseline_return_pct = baseline_data["Close"].pct_change().dropna()

    portfolio_equity_series = raw_portfolio_log["equity"]

    first_active = portfolio_equity_series.ne(
    portfolio_equity_series.iloc[0]
)

    if first_active.any():
        # find first True value
        start_idx = first_active.idxmax()
    else:
        raise RuntimeError("Cannot generate performance metrics: portfolio equity never changed.")

    equity_series = portfolio_equity_series.loc[start_idx:]


    portfolio_return_pct = equity_series.pct_change().dropna()
    return raw_trade_log, equity_series, portfolio_return_pct, baseline_return_pct
    

# ============================================================
# 1. Max Drawdown
# ============================================================

def compute_max_drawdown(equity_series: pd.Series) -> tuple[float, pd.Timestamp]:
    running_max = equity_series.cummax()
    drawdown = (equity_series / running_max) - 1
    return float(drawdown.min()), pd.Timestamp(drawdown.idxmin())


# ============================================================
# 2. Volatility (Daily Std)
# ============================================================

def compute_volatility(returns: pd.Series) -> float:
    return float(returns.std(ddof=1))


# ============================================================
# 3. Sharpe Ratio
# ============================================================

def compute_sharpe(returns: pd.Series, rf_annual: float = 0.045) -> tuple[float, float]:
    if len(returns) < 2:
        return float("nan"), float("nan")

    rf_daily = (1 + rf_annual) ** (1 / 252) - 1
    mean_r = float(returns.mean())
    std_r = float(returns.std(ddof=1))

    if std_r == 0:
        return float("nan"), float("nan")

    sharpe_period = (mean_r - rf_daily) / std_r
    sharpe_annual = sharpe_period * (252 ** 0.5)
    
    return sharpe_period, sharpe_annual


# ============================================================
# 4. Sortino Ratio
# ============================================================

def compute_sortino(returns: pd.Series, rf_annual: float = 0.045) -> tuple[float, float]:
    if len(returns) < 2:
        return float("nan"), float("nan")

    rf_daily = (1 + rf_annual) ** (1 / 252) - 1
    downside = (returns - rf_daily).clip(upper=0)

    downside_std = downside.std(ddof=1)
    if np.isclose(downside_std, 0):
        return float("nan"), float("nan")

    mean_r = float(returns.mean())
    sortino_period = (mean_r - rf_daily) / downside_std
    sortino_annual = sortino_period * (252 ** 0.5)

    return sortino_period, sortino_annual


# ============================================================
# 5. CAPM Beta, Alpha, R²
# ============================================================

def compute_capm(returns: pd.Series, market_returns: pd.Series, rf_annual: float = 0.045) -> tuple[float, float, float]:

    rf_daily = (1 + rf_annual) ** (1 / 252) - 1
    common = returns.index.intersection(market_returns.index)
    if len(common) < 2:
        return float("nan"), float("nan"), float("nan")

    rp = (returns.reindex(common).astype(float) - rf_daily)
    rm = (market_returns.reindex(common).astype(float) - rf_daily)

    x = rm.to_numpy().ravel()
    y = rp.to_numpy().ravel()


    if np.isclose(np.std(x, ddof=1), 0):
        return float("nan"), float("nan"), float("nan")

    beta, alpha_daily = np.polyfit(x, y, 1)
    alpha_annual = (1 + alpha_daily) ** 252 - 1
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2)

    return float(beta), float(alpha_annual), r2

# ============================================================
# 5. Trade Level Metrics
# ============================================================

def compute_trade_metrics(trade_log: pd.DataFrame) -> dict:
    filled_sells = trade_log[
        (trade_log["action"] == "SELL") & 
        (trade_log["status"] == "FILLED") &
        (trade_log["PnL"].notna())
    ]

    if filled_sells.empty:
        return {
            "win_rate": None,
            "avg_gain": None,
            "avg_loss": None,
            "median_gain": None,
            "median_loss": None,
            "profit_factor": None,
            "expectancy": None,
            "trade_count": 0,
        }

    wins = filled_sells[filled_sells["PnL"] > 0]["PnL"]
    losses = filled_sells[filled_sells["PnL"] < 0]["PnL"]
    count = len(filled_sells)

    win_rate = len(wins) / count if count > 0 else None

    avg_gain = float(wins.mean()) if not wins.empty else None
    avg_loss = float(losses.mean()) if not losses.empty else None
    median_gain = float(wins.median()) if not wins.empty else None
    median_loss = float(losses.median()) if not losses.empty else None

    if avg_gain is not None and avg_loss is not None and avg_loss != 0:
        profit_factor = abs(wins.sum()) / abs(losses.sum())
    else:
        profit_factor = None

    if avg_gain is not None and avg_loss is not None and win_rate is not None:
        expectancy = (avg_gain * win_rate) + (avg_loss * (1 - win_rate))
    else:
        expectancy = None

    return {
        "win_rate": float(win_rate) if win_rate is not None else None,
        "avg_gain": avg_gain,
        "avg_loss": avg_loss,
        "median_gain": median_gain,
        "median_loss": median_loss,
        "profit_factor": float(profit_factor) if profit_factor is not None else None,
        "expectancy": float(expectancy) if expectancy is not None else None,
        "trade_count": int(count),
    }

def total_performance_calculations(
    portfolio_history_path: str | Path,
    trade_log_path: str | Path,
    date: str | date,
    baseline_ticker,
) -> dict:
    """
    Compute all performance metrics from portfolio equity history.

    Loads portfolio equity history from disk, downloads benchmark data,
    and computes a fixed set of risk, return, drawdown, and CAPM metrics
    over the full active observation period.

    The observation period begins at the first date where portfolio equity
    changed from its initial value, excluding the flat pre-trade period.

    Args:
        portfolio_history_path (str or Path): Path to portfolio_history.csv.
            Required columns: date, equity
        date (str or date): The run date, recorded as metadata in the output.
        baseline_ticker (str): Market benchmark ticker used for CAPM
            calculations. Must be accessible via yfinance (e.g. "^SPX").

    Returns:
        dict: A flat dictionary of performance metrics containing:
            - volatility_daily (float): Standard deviation of daily returns.
            - sharpe_ratio_daily (float): Daily Sharpe ratio, risk-free
              adjusted at 4.5% annualized.
            - sharpe_ratio_annualized (float): Annualized Sharpe ratio
              scaled by sqrt(252).
            - sortino_ratio_daily (float): Daily Sortino ratio using
              downside deviation only.
            - sortino_ratio_annualized (float): Annualized Sortino ratio
              scaled by sqrt(252).
            - max_drawdown_pct (float): Maximum observed peak-to-trough
              equity decline as a negative percentage.
            - max_drawdown_date (str): Date of maximum drawdown.
            - capm_beta (float): Sensitivity of portfolio returns to
              benchmark returns.
            - capm_alpha_annualized (float): Annualized excess return
              beyond CAPM expectation.
            - capm_r_squared (float): Goodness of fit to the market factor.
            - start_date (str): First active equity date.
            - end_date (str): Last portfolio history date.
            - observation_count (int): Number of daily return observations.
            - generated_at (str): Run date at time of generation.

    Raises:
        RuntimeError: If portfolio_history.csv is empty, if equity never
            changed from its initial value, or if benchmark data cannot
            be downloaded.
    """
    raw_trade_log, equity_series, returns, market_returns = load_performance_data(
        portfolio_history_path, trade_log_path, baseline_ticker
    )

    # ----- Risk & Return -----
    volatility = compute_volatility(returns)
    sharpe_period, sharpe_annual = compute_sharpe(returns)
    sortino_period, sortino_annual = compute_sortino(returns)

    # ----- Max Drawdown -----
    max_drawdown, max_drawdown_date = compute_max_drawdown(equity_series)

    # ----- CAPM -----
    beta, alpha_annual, r2 = compute_capm(returns, market_returns)

    # ----- Trade Level -----
    trade_metrics = compute_trade_metrics(raw_trade_log)

# ----- Compile all metrics -----
    metrics_log = {
        # --- Risk Metrics ---
        "volatility_daily": volatility,
        "sharpe_ratio_daily": sharpe_period,
        "sharpe_ratio_annualized": sharpe_annual,
        "sortino_ratio_daily": sortino_period,
        "sortino_ratio_annualized": sortino_annual,

        # --- Drawdown ---
        "max_drawdown_pct": max_drawdown,
        "max_drawdown_date": str(max_drawdown_date),

        # --- CAPM ---
        "capm_beta": beta,
        "capm_alpha_annualized": alpha_annual,
        "capm_r_squared": r2,

        # --- Trade Level ---
        "trade_count": trade_metrics["trade_count"],
        "win_rate": trade_metrics["win_rate"],
        "avg_gain": trade_metrics["avg_gain"],
        "avg_loss": trade_metrics["avg_loss"],
        "median_gain": trade_metrics["median_gain"],
        "median_loss": trade_metrics["median_loss"],
        "profit_factor": trade_metrics["profit_factor"],
        "expectancy": trade_metrics["expectancy"],

        # --- Metadata ---
        "start_date": str(equity_series.index[0]),
        "end_date": str(equity_series.index[-1]),
        "observation_count": len(returns),
        "generated_at": str(date),
    }

    return metrics_log