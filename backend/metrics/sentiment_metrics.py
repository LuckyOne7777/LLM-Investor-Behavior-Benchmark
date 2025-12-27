import pandas as pd
from pysentiment2 import LM
from pathlib import Path
from datetime import date

def file_to_text(path: Path) -> str:
    text = ""
    try:
        with open(path, "r") as f:
            text = f.read()
            f.close()
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find file path for {path}")
    
    return text
def get_score(text: str) -> tuple[dict, list]:
    lm = LM()
    tokens: list = lm.tokenize(text)
    score:  dict = lm.get_score(tokens)
    return score, tokens

def evaluate_sentiment(score: dict, tokens: list, date: date, report_type: str="Unknown") -> dict:
    word_count = max(len(tokens), 1)

    log = {
        "subjectivity": float(score['Subjectivity']),
        "polarity": float(score['Polarity']),
        "positive_count": int(score['Positive']),
        "negative_count": int(score['Negative']),
        "token_count": int(word_count),
        "report_type": report_type,
        "date": str(date),
    }
    return log

def analyze_sentiment(text: str, date: date, report_type: str="Unknown") -> dict:
    score, tokens = get_score(text)
    return evaluate_sentiment(score, tokens, date, report_type=report_type)

def narrative_drift(weekly_summaries):
    """
    Measures sentiment volatility between weekly research outputs.
    Input:
        weekly_summaries: list of text strings
    Output:
        float
    """
    # TODO: sentiment extraction + drift
    return 0.0