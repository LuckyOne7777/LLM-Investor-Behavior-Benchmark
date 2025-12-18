import pandas as pd 
from pathlib import Path
import json
import re 

DAILY_UPDATES_FILE_NAME = Path(f"daily_update - {pd.Timestamp.now().date()}.txt")
PORTFOLIO_FILE_NAME = f"portfolio.csv"
DEEP_RESEARCH_FILE_NAME = Path(f"deep_research - {pd.Timestamp.now().date()}.txt")
ORDERS_FILE_NAME = f"pending_trades.csv"

def portfolio_exists(model_name: str):

    path = Path(f"models/{model_name}") / PORTFOLIO_FILE_NAME
    try:
        portfolio = pd.read_csv(path)
        if portfolio.empty:
            return(False)
        else:
            return(True)
    except:
        return(False)
def save_deep_research(txt: str, model: str):

    path_to_deep_research = Path(f"models/{model}/research/deep_research")
    full_path = path_to_deep_research / DEEP_RESEARCH_FILE_NAME
    file = open(full_path, "w")
    file.write(txt)
    file.close()
    return
def save_daily_updates(txt: str, model: str):

    path_to_daily_updates = Path(f"models/{model}/research/daily_updates")
    full_path = path_to_daily_updates / DAILY_UPDATES_FILE_NAME
    file = open(full_path, "w")
    file.write(txt)
    file.close()
    return

def parse_json(text: str, tag: str):
    # Extract the block from given section
    pattern = rf"<{re.escape(tag)}>\s*(\{{.*?\}})\s*</{re.escape(tag)}>"
    match = re.search(pattern, text, flags=re.DOTALL)
    
    if not match:
        raise ValueError("No ORDERS_JSON block found.")

    json_str = match.group(1)

    # Optional: fix trailing commas
    json_str = re.sub(r",\s*}", "}", json_str)

    return json.loads(json_str)

def save_orders(orders_dict: str, model_name: str):
    path = Path(f"models/{model_name}") / ORDERS_FILE_NAME
    f = open(path, "w")
    f.write(orders_dict)
    f.close()
    return

def delete_orders(model_name: str):
    path = Path(f"models/{model_name}") / ORDERS_FILE_NAME
    f = open(path, "w")
    f.close()
    return
def load_orders(model_name: str):
    path = Path(f"models/{model_name}") / ORDERS_FILE_NAME
    return pd.read_csv(path)
