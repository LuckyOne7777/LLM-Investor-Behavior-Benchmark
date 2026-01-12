from datetime import datetime, timedelta, date
import pandas as pd
from pathlib import Path

def _recent_execution_logs(trade_log_path: str | Path, date: date | None = None, look_back: int = 5) -> pd.DataFrame:
    """
    Return execution log entries within a recent lookback window.

    This internal helper loads a trade execution log from disk and filters
    entries whose execution date falls within the last `look_back` days
    relative to a reference date.

    The function always returns a pandas DataFrame. If no executions fall
    within the specified window, the returned DataFrame will be empty.

    Parameters
    ----------
    trade_log_path : str or pathlib.Path
        Path to the trade execution log CSV file. The file must contain a
        column named "date".

    date : datetime.date or None, optional
        Reference date used to compute the lookback window. If None, the
        current system date is used.

    look_back : int, optional
        Number of days to look back from the reference date (inclusive).
        Defaults to 5.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing execution log entries whose dates fall within
        the specified lookback window. The DataFrame will be empty if no
        matching records are found.

    Notes
    -----
    - The "date" column is parsed and normalized to date-only values.
    - This function performs no presentation or user-facing formatting.
    - Callers are responsible for providing normalized inputs and handling
      empty results.
    """
    if date is None:
        TODAY = pd.Timestamp.now().date()
    else:
        TODAY = pd.Timestamp(date).date() 
    time_range = TODAY - timedelta(days=look_back)
    trade_log = pd.read_csv(trade_log_path)
    trade_log["date"] = pd.to_datetime(trade_log["date"]).dt.date
    return trade_log[trade_log["date"] >= time_range]