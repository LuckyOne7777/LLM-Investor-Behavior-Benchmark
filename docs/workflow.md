# Workflow

Learn everything from putting together your workflow to accessing exposed variables for prompts.
All of the coding examples are from the `user_side` folder;
feel free to use the examples as inspiration or copy line by line.  
## Needed for Workflow

- prompt skeletons
- functions for inputting prompts
- checking design limitations in important-notes.md


## Example Workflow

The following functions are from `user_side/workflow.py`:

### Weekly Workflow

```python

    MODELS = ["deepseek", "gpt-4.1"]

    def weekly_flow():

    for model in MODELS:
        # set up object
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}")
        # essential processing that should always be first (only use this processing function)
        libb.process_portfolio()
        # getting output from user created function
        deep_research_report = prompt_deep_research(libb)
        libb.save_deep_research(deep_research_report)

        orders_json = parse_json(deep_research_report, "ORDERS_JSON")

        libb.save_orders(orders_json)
        libb.analyze_sentiment(deep_research_report)
    return
```
---
### Daily Workflow

```python

def daily_flow():
    for model in MODELS:
        libb = LIBBmodel(f"user_side/runs/run_v1/{model}")
        libb.process_portfolio()
        daily_report = prompt_daily_report(libb)
        libb.analyze_sentiment(daily_report)
        libb.save_daily_update(daily_report)

        orders_json = parse_json(daily_report, "ORDERS_JSON")

        libb.save_orders(orders_json)
    return
```
