import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

API_V1_BASE_ROUTE = os.getenv("API_V1_BASE_ROUTE", "/api/v1")
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", 8000))

API_HTTP_BASE_URL = f'http://{API_HOST}:{API_PORT}{API_V1_BASE_ROUTE}'