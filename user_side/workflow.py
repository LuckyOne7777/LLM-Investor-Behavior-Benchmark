from libb.model import LIBBmodel
from .prompt_models import prompt_daily_report, prompt_deep_research
from libb.other.parse import parse_json
import pandas as pd

MODELS = ["deepseek", "gpt-4.1"]

def weekly_flow():

    for model in MODELS:
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}", date="2025-12-13")
        libb.process_portfolio()
        deep_research_report = prompt_deep_research(libb)
        libb.save_deep_research(deep_research_report)

        orders_json = parse_json(deep_research_report, "ORDERS_JSON")

        libb.save_orders(orders_json)
        libb.analyze_sentiment(deep_research_report)
    return

def daily_flow():
    for model in MODELS:
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}", date="2025-12-13")
        libb.reset_run()
        libb.ensure_file_system()
        """
        libb.process_portfolio()
        daily_report = prompt_daily_report(libb)
        libb.analyze_sentiment(daily_report)
        libb.save_daily_update(daily_report)

        orders_json = parse_json(daily_report, "ORDERS_JSON")

        libb.save_orders(orders_json)
        """
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