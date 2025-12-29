import pandas as pd
from pathlib import Path
from types_file import Order

def load_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

def append_log(path: Path, row: dict) -> None:
    df = load_df(path)
    if not df.empty:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(path, index=False)

def catch_missing_order_data(order: Order, required_cols: list, trade_log_path: Path) -> bool:
    """Log failures for missing or null required order data. Return True if needed data is in order."""
    action = order["action"]
    if action == "b":
        action = "BUY"
    elif action == "s":
        action = "SELL"
    elif action == "u":
        action = "UPDATE"
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
    else:
        return True