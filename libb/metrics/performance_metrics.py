import numpy as np
import pandas as pd
import json
from datetime import date
from pathlib import Path
import yfinance as yf

def load_performance_data(portfolio_history_path: Path | str, baseline_ticker: str) -> tuple[pd.Series, pd.Series, pd.Series]:
    raw_portfolio_log = pd.read_csv(portfolio_history_path, parse_dates=["date"])
    raw_portfolio_log = raw_portfolio_log.set_index("date")
    if raw_portfolio_log.empty:
        raise RuntimeError("Cannot generate performance metrics: `portfolio_history.csv` is empty.")
    
    first_date = raw_portfolio_log.index[0]
    last_date = raw_portfolio_log.index[-1]

    baseline_data = yf.download(baseline_ticker, start=first_date, end=last_date, auto_adjust=True, progress=False)
    if baseline_data is None:
        raise RuntimeError(f"Cannot generate performance metrics: ticker data {baseline_ticker} was type None.")

    baseline_return_pct = baseline_data["Close"].pct_change().dropna()
    portfolio_equity_series = raw_portfolio_log["equity"]
    portfolio_return_pct = portfolio_equity_series.pct_change().dropna()
    return portfolio_equity_series, portfolio_return_pct, baseline_return_pct
    

# ============================================================
# 1. Max Drawdown
# ============================================================

def compute_max_drawdown(equity_series: pd.Series) -> tuple[float, pd.Timestamp]:
    running_max = equity_series.cummax()
    drawdown = (equity_series / running_max) - 1
    return float(drawdown.min()), drawdown.idxmin()


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

    downside_std = (downside.pow(2).mean()) ** 0.5
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
    rf_daily = ((1 + rf_annual)** 1/252) - 1
    common = returns.index.intersection(market_returns.index)
    if len(common) < 2:
        return float("nan"), float("nan"), float("nan")

    rp = (returns.reindex(common).astype(float) - rf_daily)
    rm = (market_returns.reindex(common).astype(float) - rf_daily)

    x = rm.values
    y = rp.values

    x = rm.to_numpy().ravel()
    y = rp.to_numpy().ravel()


    if np.isclose(np.std(x, ddof=1), 0):
        return float("nan"), float("nan"), float("nan")

    beta, alpha_daily = np.polyfit(x, y, 1)
    alpha_annual = (1 + alpha_daily) ** 252 - 1
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2)

    return float(beta), float(alpha_annual), r2

def total_performance_calculations(
    portfolio_history_path: str | Path,
    date: str | date,
    baseline_ticker,
) -> dict:
    equity_series, returns, market_returns = load_performance_data(portfolio_history_path, baseline_ticker)
    
    # ----- Risk & Return -----
    volatility = compute_volatility(returns)
    sharpe_period, sharpe_annual = compute_sharpe(returns)
    sortino_period, sortino_annual = compute_sortino(returns)

    # ----- Max Drawdown -----
    max_drawdown, max_drawdown_date = compute_max_drawdown(equity_series)

    # ----- CAPM -----
    beta, alpha_annual, r2 = compute_capm(returns, market_returns)

    # ----- Compile all metrics -----
    metrics_log = {
        "volatility": volatility,
        "sharpe_period": sharpe_period,
        "sharpe_annual": sharpe_annual,
        "sortino_period": sortino_period,
        "sortino_annual": sortino_annual,
        "max_drawdown": max_drawdown,
        "max_drawdown_date": str(max_drawdown_date),
        "beta": beta,
        "alpha_annual": alpha_annual,
        "r2": r2,
        "portfolio_start_date": str(equity_series.index[0]),
        "portfolio_end_date": str(equity_series.index[-1]),
        "days_of_data": len(equity_series),  
        "run_date_generated": str(date)
    }

    return metrics_log
