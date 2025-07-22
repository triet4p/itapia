import os
from dotenv import load_dotenv
from pathlib import Path

# ENV Config
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

AI_QUICK_V1_BASE_ROUTE = os.getenv("AI_QUICK_V1_BASE_ROUTE", "/api/v1")

# Kaggle model version control config
KAGGLE_KEY = os.getenv("KAGGLE_KEY")
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
MODEL_FRAMEWORK = 'scikitLearn'
MODEL_VARIATION = 'default'
MODEL_HANDLE_TEMPLATE = '{kaggle_username}/{model_slug}/{framework}/{variation}'
MODEL_SLUG_TEMPLATE = 'itapia-final-{id}'
MODEL_MAIN_MODEL_FILE = 'final-model.pkl'
MODEL_METADATA_FILE = 'metadata.json'
MODEL_SNAPSHOTS_TEMPLATE = "snapshots/model_fold_{fold_id}.pkl"
LOCAL_ARTIFACTS_BASE_PATH = './artifacts'
TASK_ID_SECTOR_TEMPLATE = '{problem}-{sector}'
TRIPLE_BARRIER_PROBLEM_ID = 'clf-triple-barrier'
REG_5D_DIS_PROBLEM_ID = 'reg-5d-dis'
REG_20D_DIS_PROBLEM_ID = 'reg-20d-dis'