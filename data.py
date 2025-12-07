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