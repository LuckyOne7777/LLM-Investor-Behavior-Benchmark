import pandas as pd 
from pathlib import Path
def portfolio_exists(model_name: str):
    PORTFOLIO_FILE_NAME = f"{model_name}/portfolio.csv"
    path = Path("models") / PORTFOLIO_FILE_NAME
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
save_deep_research("ahh", "gpt-5")