import pandas as pd
import numpy as np
from pysentiment2 import LM
import pdfplumber

def file_to_text(path):
    text = ""
    try:
        with open(path, "r") as f:
            text = f.read()
            f.close()
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find file path for {path}")
    
    return text
def get_score(text: str):
    lm = LM()
    tokens = lm.tokenize(text)
    score = lm.get_score(tokens)
    return score, tokens

def evaluate_sentiment(score, tokens, report_type="Unknown"):
    word_count = max(len(tokens), 1)

    log = {
        "subjectivity": score['Subjectivity'],
        "polarity": score['Polarity'],
        "positive_count": score['Positive'],
        "negative_count": score['Negative'],
        "token_count": word_count,
        "report_type": report_type,
        "date": pd.Timestamp.now().date(),
    }
    return log

def analyze_sentiment(text, report_type="Unknown"):
    score, tokens = get_score(text)
    return evaluate_sentiment(score, tokens, report_type=report_type)





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