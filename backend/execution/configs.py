import os

def activate_models():
    ACTIVE_MODELS = {}
    if os.getenv("OPENAI_API_KEY") is not None:
        ACTIVE_MODELS["baseline"] = {"provider": "openai", 
                                     "model":"gpt-4.1-mini"}
    if os.getenv("DEEPSEEK_API_KEY") is not None:
        ACTIVE_MODELS["alt"] = {"provider": "deepseek", 
                                "model":"deepseek-chat"}
    if ACTIVE_MODELS.empty:
        raise RuntimeError("""No APIs keys set. Please set your env vars for 
        'DEEPSEEK_API_KEY' and/or 'OPENAI_API_KEY'. """)
    return ACTIVE_MODELS
    
