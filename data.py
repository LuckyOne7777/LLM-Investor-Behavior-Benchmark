import pandas as pd 
from pathlib import Path
import json
import re 
def portfolio_exists(model_name: str):
    PORTFOLIO_FILE_NAME = f"portfolio.csv"
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

    DEEP_RESEARCH_FILE_NAME = Path(f"Deep Research - {pd.Timestamp.now().date()}.txt")
    path_to_deep_research = Path(f"models/{model}/Research/Deep Research")
    full_path = path_to_deep_research / DEEP_RESEARCH_FILE_NAME
    file = open(full_path, "w")
    file.write(txt)
    file.close()
    return
def save_daily_updates(txt: str, model: str):

    DAILY_UPDATES_FILE_NAME = Path(f"Daily Update - {pd.Timestamp.now().date()}.txt")
    path_to_daily_updates = Path(f"models/{model}/Research/Daily Updates")
    full_path = path_to_daily_updates / DAILY_UPDATES_FILE_NAME
    file = open(full_path, "w")
    file.write(txt)
    file.close()
    return

def parse_orders_json(text: str):
    # Extract the <ORDERS_JSON>...</ORDERS_JSON> section
    match = re.search(r"<ORDERS_JSON>\s*(\{.*?\})\s*</ORDERS_JSON>", 
                      text, flags=re.DOTALL)
    
    if not match:
        raise ValueError("No ORDERS_JSON block found.")

    json_str = match.group(1)

    # Optional: fix trailing commas
    json_str = re.sub(r",\s*}", "}", json_str)

    return json.loads(json_str)

def save_orders(json_str: str, model_name: str):
    ORDERS_FILE_NAME = f"pending_trades.csv"
    path = Path(f"models/{model_name}") / ORDERS_FILE_NAME
    f = open(path, "w")
    f.write(json_str)
    f.close
    return

def load_orders(model_name: str):
    ORDERS_FILE_NAME = f"pending_trades.csv"
    path = Path(f"models/{model_name}") / ORDERS_FILE_NAME
    return pd.read_csv(path)