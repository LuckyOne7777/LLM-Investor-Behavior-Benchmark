from libb.model import LIBBmodel
from .prompt_models import prompt_daily_report, prompt_deep_research
from libb.other.parse import parse_json
import pandas as pd

MODELS = ["deepseek", "gpt-4.1"]

def weekly_flow():

    for model in MODELS:
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}")
        libb.process_portfolio()
        report = prompt_deep_research(libb)
        libb.analyze_sentiment(report)

        orders_json = parse_json(report, "ORDERS_JSON")

        libb.save_deep_research(report)
        libb.save_orders(orders_json)
    return

def daily_flow():
    for model in MODELS:
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}")
        libb.process_portfolio()
        report = prompt_daily_report(libb)
        libb.analyze_sentiment(report)

        orders_json = parse_json(report, "ORDERS_JSON")

        libb.save_daily_update(report)
        libb.save_orders(orders_json)
    return

today = pd.Timestamp.now().date()
day_num = today.weekday()

if day_num  == 4: # Friday
    weekly_flow()
elif day_num < 4:
    daily_flow() # Mon-Thursday
else:  # Weekend
    pass
print("Success!")