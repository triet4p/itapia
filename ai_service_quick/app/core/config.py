import os
from dotenv import load_dotenv
from pathlib import Path

# ENV Config
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GATEWAY_V1_BASE_ROUTE = os.getenv("GATEWAY_V1_BASE_ROUTE", "/api/v1")
GATEWAY_HOST = os.getenv("GATEWAY_HOST", "localhost")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8000))
GATEWAY_HTTP_BASE_URL = f'http://{GATEWAY_HOST}:{GATEWAY_PORT}{GATEWAY_V1_BASE_ROUTE}'

AI_QUICK_V1_BASE_ROUTE = os.getenv("AI_QUICK_V1_BASE_ROUTE", "/api/v1")

# Kaggle model version control config
KAGGLE_KEY = os.getenv("KAGGLE_KEY")
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
MODEL_FRAMEWORK = 'scikitLearn'
MODEL_VARIATION = 'default'
MODEL_HANDLE_TEMPLATE = '{kaggle_username}/{model_slug}/{framework}/{variation}'
MODEL_SLUG_TEMPLATE = 'itapia-test-{id}'
MODEL_MAIN_MODEL_FILE = 'final-model.pkl'
MODEL_METADATA_FILE = 'metadata.json'
MODEL_SNAPSHOTS_TEMPLATE = "snapshots/model_fold_{fold_id}.pkl"
LOCAL_ARTIFACTS_BASE_PATH = './artifacts'