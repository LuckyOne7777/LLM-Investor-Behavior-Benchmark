from openai import OpenAI
import os

def prompt_orchestration(model_path, text):
    model = model_path.replace("runs/run_v1", "")
    if model == "deepseek":
        return prompt_deepseek(text)
    elif model == "gpt-4.1":
        return prompt_chatgpt(text)

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