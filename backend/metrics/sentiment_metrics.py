import pandas as pd
import numpy as np
from pysentiment2 import LM
import pdfplumber

def file_to_text(path):
    text = ""
    with open(path, "r") as f:
        text = f.read()
        f.close()
    
    return text
def get_score(text: str):
    lm = LM()
    tokens = lm.tokenize(text)
    score = lm.get_score(tokens)
    return score


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