import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Cấu hình CLient
# Cấu hình CLient
AI_SERVICE_QUICK_HOST = os.getenv("AI_QUICK_HOST", 'localhost')
AI_SERVICE_QUICK_PORT = os.getenv("AI_QUICK_PORT", 8000)
AI_SERVICE_QUICK_V1_BASE_ROUTE = os.getenv("AI_QUICK_V1_BASE_ROUTE", "/api/v1")
AI_SERVICE_QUICK_BASE_URL = f'http://{AI_SERVICE_QUICK_HOST}:{AI_SERVICE_QUICK_PORT}{AI_SERVICE_QUICK_V1_BASE_ROUTE}'

EVO_WORKER_HOST = os.getenv("EVO_WORKER_HOST", 'localhost')
EVO_WORKER_PORT = os.getenv("EVO_WORKER_PORT", 8000)
EVO_WORKER_V1_BASE_ROUTE = os.getenv("EVO_WORKER_V1_BASE_ROUTE", "/api/v1")
EVO_WORKER_BASE_URL = f'http://{EVO_WORKER_HOST}:{EVO_WORKER_PORT}{EVO_WORKER_V1_BASE_ROUTE}'

EVO_REGEN_BACKTEST_DATA = os.getenv("EVO_REGEN_BACKTEST_DATA", 'false').lower() in ['true', '1', 'yes', 'y', 't']

SELECTOR_START_DATE = datetime(2019, 9, 1)
SELECTOR_END_DATE = datetime(2025, 3, 31)
MONTHLY_DAY = 10
MAX_SPECIAL_POINTS = 50
POLLING_INTERVAL_SECONDS = 45
PARALLEL_CONCURRENCY_LIMIT = 1

PARALLEL_MULTICONTEXT_LIMIT = 5

RANDOM_SEED = 42
INIT_TERMINAL_PROB = 0.15