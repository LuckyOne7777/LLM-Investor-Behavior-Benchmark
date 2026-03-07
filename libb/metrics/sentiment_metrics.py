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
    """
    Analyze sentiment for the given text using the Loughran-McDonald
    financial sentiment lexicon.

    Args:
        text (str): Text to analyze. Typically raw model output from
            a daily or weekly research report.
        date (date): The run date, recorded as metadata in the output.
        report_type (str): Identifier describing the source or type of
            the report. Defaults to "Unknown".

    Returns:
        dict: Sentiment log containing:
            - subjectivity (float): Ratio of opinion-bearing tokens to
              total tokens. Range 0.0 to 1.0.
            - polarity (float): Net sentiment score, positive minus
              negative normalized by total tokens. Range -1.0 to 1.0.
            - positive_count (int): Number of positive tokens identified
              by the Loughran-McDonald lexicon.
            - negative_count (int): Number of negative tokens identified
              by the Loughran-McDonald lexicon.
            - token_count (int): Total number of tokens in the text.
            - report_type (str): Source or type of the report as provided.
            - date (str): Run date at time of analysis.
    """

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