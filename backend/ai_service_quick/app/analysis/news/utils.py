"""Utility functions for news analysis."""

import re
from pathlib import Path
from typing import List, Set

import pandas as pd


def load_dictionary(filepath: str) -> Set[str]:
    """Read a CSV dictionary file and return a set of normalized words.

    Args:
        filepath (str): Path to the dictionary CSV file

    Returns:
        Set[str]: Set of normalized words from the dictionary

    Raises:
        FileNotFoundError: If the dictionary file is not found
    """
    file_path = Path(filepath)
    if not file_path.exists():
        raise FileNotFoundError(f"Dictionary file not found at: {file_path}")

    df = pd.read_csv(file_path, header=None)
    return set(df.iloc[:, 0].str.lower())


def preprocess_news_texts(texts: List[str]) -> List[str]:
    """Clean a list of news texts before analysis.

    - Convert to lowercase
    - Remove ticker symbols in parentheses

    Args:
        texts (List[str]): List of news texts to clean

    Returns:
        List[str]: List of cleaned news texts
    """
    cleaned_texts = []
    # Regular expression to find an optional space, opening parenthesis,
    # alphanumeric characters inside, and a closing parenthesis
    ticker_pattern = re.compile(r"\s*\([A-Z0-9\.]+\)")

    for text in texts:
        # 1. Remove ticker symbols
        no_tickers_text = ticker_pattern.sub("", text)
        # 2. Convert to lowercase
        lower_text = no_tickers_text.lower()
        cleaned_texts.append(lower_text)

    return cleaned_texts
