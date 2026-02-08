import numpy as np
import pandas as pd
import json
from datetime import date


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
    if downside_std == 0:
        return float("nan"), float("nan")

    mean_r = float(returns.mean())
    sortino_period = (mean_r - rf_daily) / downside_std
    sortino_annual = sortino_period * (252 ** 0.5)

    return sortino_period, sortino_annual


# ============================================================
# 5. CAPM Beta, Alpha, R²
# ============================================================

def compute_capm(returns: pd.Series, market_returns: pd.Series, rf_daily: float) -> tuple[float, float, float]:
    common = returns.index.intersection(market_returns.index)
    if len(common) < 2:
        return float("nan"), float("nan"), float("nan")

    rp = (returns.reindex(common).astype(float) - rf_daily)
    rm = (market_returns.reindex(common).astype(float) - rf_daily)

    x = rm.values
    y = rp.values

    if np.std(x, ddof=1) == 0:
        return float("nan"), float("nan"), float("nan")

    beta, alpha_daily = np.polyfit(x, y, 1)
    alpha_annual = (1 + alpha_daily) ** 252 - 1
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2)

    return float(beta), float(alpha_annual), r2

def total_performance_calculations(
    returns: pd.Series,
    equity_series: pd.Series,
    market_returns: pd.Series,
    rf_daily: float,
    date: str | date | None = None, 
) -> dict:
    # ----- Risk & Return -----
    volatility = compute_volatility(returns)
    sharpe_period, sharpe_annual = compute_sharpe(returns)
    sortino_period, sortino_annual = compute_sortino(returns)

    # ----- Max Drawdown -----
    max_drawdown, max_drawdown_date = compute_max_drawdown(equity_series)

    # ----- CAPM -----
    beta, alpha_annual, r2 = compute_capm(returns, market_returns, rf_daily)

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
        "date": pd.Timestamp.now().date()
    }
    metrics_log = json.load(metrics_log)

    return metrics_log
