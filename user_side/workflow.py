from backend.LIBB import LIBBmodel
from .prompt_models import prompt_orchestration
MODELS = ["deepseek", "gpt-4.1"]
# to be done on friday after trading
# following is a basic skeleton, file names and parameters may be incorrect
def weekly_workflow():
    """
    for model in MODELS:
        libb = LIBBmodel(f"runs/run_v1/{model}")
        libb.process_portfolio()
        report = prompt_orchestration(libb.model_path)
        report_path = libb.save_deep_research(report)
        libb.analyze_report(report_path)
        libb.calculate_metrics()
        orders_json = parse_json(text)
        libb.save_orders(orders_json)
    """
    return

def daily_flow():
    """
    for model in MODELS:
        libb = LIBBmodel(f"runs/run_v1/{model}")
        libb.process_portfolio()
        report = prompt_orchestration(libb.model_path)
        report_path = libb.save_daily_report(report)
        libb.analyze_report(report_path)
        orders_json = parse_json(text)
        libb.save_orders(orders_json)
    """
    return