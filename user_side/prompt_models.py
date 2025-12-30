from openai import OpenAI
import os
from datetime import datetime
from .deep_research_prompt import create_deep_research_prompt
from .daily_research_prompt import create_daily_prompt

def prompt_deepseek(text, model="deepseek-chat"):

    client = OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"),
                    base_url="https://api.deepseek.com")
    
    response = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": text}], temperature=0.0,
        stream=False)
    return response.choices[0].message.content
    
def prompt_chatgpt(text, model="gpt-4.1-mini"):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": text}], temperature=0.0,
        stream=False)
    return response.choices[0].message.content

def prompt_deep_research(libb):
    model = libb._model_path.replace("user_side/runs/run_v1/", "")
    text = create_deep_research_prompt(libb)
    if model == "deepseek":
        return prompt_deepseek(text)
    elif model == "gpt-4.1":
        return prompt_chatgpt(text)
    else:
        raise RuntimeError(f"Unidentified model: {model}")

def prompt_daily_report(libb):
    model = libb._model_path.replace("user_side/runs/run_v1/", "")
    text = create_daily_prompt(libb)
    if model == "deepseek":
        return prompt_deepseek(text)
    elif model == "gpt-4.1":
        return prompt_chatgpt(text)
    else:
        raise RuntimeError(f"Unidentified model: {model}")