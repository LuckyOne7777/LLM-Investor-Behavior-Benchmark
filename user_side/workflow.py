from backend.LIBB import LIBBmodel
from .prompt_models import prompt_daily_report, prompt_deep_research
from .parse import parse_json

MODELS = ["deepseek", "gpt-4.1"]

def weekly_workflow():

    for model in MODELS:
        libb = LIBBmodel(f"runs/run_v1/{model}")
        libb.process_portfolio()
        report = prompt_deep_research(libb)
        libb.analyze_report(report)

        orders_json = parse_json(report, "ORDERS_JSON")

        libb.save_deep_research(report)
        libb.save_orders(orders_json)

    return

def daily_flow():
    for model in MODELS:
        libb = LIBBmodel(f"runs/run_v1/{model}")
        libb.process_portfolio()
        report = prompt_daily_report(libb)
        libb.analyze_report(report)

        orders_json = parse_json(report, "ORDERS_JSON")

        libb.save_daily_report(report)
        libb.save_orders(orders_json)
    return

