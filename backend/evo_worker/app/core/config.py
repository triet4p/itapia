import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Cấu hình CLient
AI_SERVICE_QUICK_HOST = os.getenv("AI_QUICK_HOST", 'localhost')
AI_SERVICE_QUICK_PORT = os.getenv("AI_QUICK_PORT", 8000)
AI_SERVICE_QUICK_V1_BASE_ROUTE = os.getenv("AI_QUICK_V1_BASE_ROUTE", "/api/v1")
AI_SERVICE_QUICK_BASE_URL = f'http://{AI_SERVICE_QUICK_HOST}:{AI_SERVICE_QUICK_PORT}{AI_SERVICE_QUICK_V1_BASE_ROUTE}'

SELECTOR_START_DATE = datetime(2019, 9, 1)
SELECTOR_END_DATE = datetime(2025, 3, 31)
MONTHLY_DAY = 10
MAX_SPECIAL_POINTS = 50
POLLING_INTERVAL_SECONDS = 45
PARALLEL_CONCURRENCY_LIMIT = 1