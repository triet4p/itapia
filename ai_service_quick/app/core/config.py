import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GATEWAY_V1_BASE_ROUTE = os.getenv("GATEWAY_V1_BASE_ROUTE", "/api/v1")
GATEWAY_HOST = os.getenv("GATEWAY_HOST", "localhost")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8000))
GATEWAY_HTTP_BASE_URL = f'http://{GATEWAY_HOST}:{GATEWAY_PORT}{GATEWAY_V1_BASE_ROUTE}'

AI_QUICK_V1_BASE_ROUTE = os.getenv("AI_QUICK_V1_BASE_ROUTE", "/api/v1")