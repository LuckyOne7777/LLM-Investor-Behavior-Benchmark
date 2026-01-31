from openai import OpenAI
import os
from datetime import datetime
from ..prompts.deep_research_prompt import create_deep_research_prompt
from ..prompts.daily_research_prompt import create_daily_prompt

from openai import OpenAI
import os

def prompt_deepseek(text: str, model: str = "deepseek-chat") -> str:

    deepseek_client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",)
    
    response = deepseek_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": text}],
        temperature=0.0,
    )

    if not response.choices:
        raise RuntimeError("No choices returned from DeepSeek.")

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("Output from DeepSeek was None.")

    return content


def prompt_chatgpt(text: str, model: str = "gpt-4.1-mini") -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": text}],
        temperature=0.0,
    )

    if not response.choices:
        raise RuntimeError("No choices returned from ChatGPT.")

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("Output from ChatGPT was None.")

    return content

def prompt_deep_research(libb) -> str:
    model = libb._model_path.replace("user_side/runs/run_v1/", "")
    text = create_deep_research_prompt(libb)
    if model == "deepseek":
        return prompt_deepseek(text)
    elif model == "gpt-4.1":
        return prompt_chatgpt(text)
    else:
        raise RuntimeError(f"Unidentified model: {model}")

def prompt_daily_report(libb) -> str:
    model = libb._model_path.replace("user_side/runs/run_v1/", "")
    text = create_daily_prompt(libb)
    if model == "deepseek":
        return prompt_deepseek(text)
    elif model == "gpt-4.1":
        return prompt_chatgpt(text)
    else:
        raise RuntimeError(f"Unidentified model: {model}")