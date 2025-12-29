import pandas as pd
from pathlib import Path
from types_file import Order

def load_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

def append_log(path: Path, row: dict) -> None:
    df = load_df(path)
    row_df = pd.DataFrame([row])
    if not df.empty:
        row_df.to_csv(path, index=False, mode="a", header=False)
    else:
        df = pd.DataFrame([row])
        df.to_csv(path, index=False)

def catch_missing_order_data(order: Order, required_cols: list, trade_log_path: Path) -> bool:
    """Log failures for missing or null data required for order.
    Return True if needed data exists; False otherwise.
    """
    action_map = {"b": "BUY", "s": "SELL", "u": "UPDATE"}
    action = action_map.get(order["action"], order["action"])

    missing_cols = []
    for col in required_cols:
        if col not in order or order[col] is None:
            missing_cols.append(col)

    if missing_cols:
        append_log(trade_log_path, {
            "Date": order["date"],
            "Ticker": order["ticker"],
            "Action": action,
            "Status": "FAILED",
            "Reason": f"MISSING OR NULL ORDER INFO: {missing_cols}"
        })
        return False

    return True
