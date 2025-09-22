import os
from pathlib import Path

from dotenv import load_dotenv

# ENV Config
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

AI_QUICK_V1_BASE_ROUTE = os.getenv("AI_QUICK_V1_BASE_ROUTE", "/api/v1")

# Kaggle model version control config
KAGGLE_KEY = os.getenv("KAGGLE_KEY")
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
MODEL_FRAMEWORK = "scikitLearn"
MODEL_VARIATION = "original"
MODEL_HANDLE_TEMPLATE = "{kaggle_username}/{model_slug}/{framework}/{variation}"
MODEL_SLUG_TEMPLATE = "itapia-final-{id}"
MODEL_MAIN_MODEL_FILE = "final-model.pkl"
MODEL_METADATA_FILE = "metadata.json"
MODEL_SNAPSHOTS_TEMPLATE = "snapshots/model_fold_{fold_id}.pkl"
LOCAL_ARTIFACTS_BASE_PATH = "./artifacts"
TASK_ID_SECTOR_TEMPLATE = "{problem}-{sector}"
TRIPLE_BARRIER_PROBLEM_ID = "clf-triple-barrier"
REG_5D_DIS_PROBLEM_ID = "reg-5d-dis"
REG_20D_DIS_PROBLEM_ID = "reg-20d-dis"


FORECASTING_TRAINING_BONUS_FEATURES = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "RSI_14",
    "ATRr_14",
    "SMA_50",
    "SMA_200",
    "diff_from_sma_50",
    "diff_from_sma_200",
    "CDL_ENGULFING",
    "CDL_3BLACKCROWS",
    "CDL_3WHITESOLDIERS",
    "CDL_MORNINGSTAR",
    "CDL_EVENINGSTAR",
]

FORECASTING_TRAINING_SCORE_WEIGHTS = {"lgbm": 0.4, "rf": 0.3, "mi": 0.3}

LGBM_MODEL_BASE_NAME = "LGBM"
MULTIOUTPUT_LGBM_MODEL_BASE_NAME = "Multi-LGBM"

NEWS_SENTIMENT_ANALYSIS_MODEL = (
    "AnkitAI/distilbert-base-uncased-financial-news-sentiment-analysis"
)
NEWS_TRANSFORMER_NER_MODEL = "dslim/distilbert-NER"
NEWS_NER_SCORE_THRESHOLD = 0.75
NEWS_SPACY_NER_MODEL = "en_core_web_md"
NEWS_IMPACT_ASSESSMENT_MODEL = "custom-word-based-impact-assessment"
NEWS_IMPACT_DICTIONARY_PATH = (
    "/ai-service-quick/app/analysis/news/dictionaries/impact_{level}.csv"
)
NEWS_KEYWORD_HIGHLIGHT_MODEL = "custom-word-based-keyword-highlight"
NEWS_KEYWORD_HIGHLIGHT_PATH = (
    "/ai-service-quick/app/analysis/news/dictionaries/keyword_{direction}.csv"
)
NEWS_RESULT_SUMMARY_MODEL = "custom-result-summarizer"

NEWS_COUNT_RELEVANT = 10
NEWS_COUNT_CONTEXTUAL = 4
NEWS_COUNT_MACRO = 2
NEWS_TOTAL_LIMIT = 17

BACKTEST_DAY_OF_MONTH = 10
BACKTEST_START_YEAR = 2020
BACKTEST_END_YEAR = 2024
