# common/dblib/config.py
"""Database configuration settings for the application.

This module loads environment variables and defines database connection settings
for both PostgreSQL and Redis, as well as table names used throughout the application.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# PostgreSQL Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Table Names
DAILY_PRICES_TABLE_NAME = 'daily_prices'
RELEVANT_NEWS_TABLE_NAME = 'relevant_news'
UNIVERSAL_NEWS_TABLE_NAME = 'universal_news'
INTRADAY_STREAM_PREFIX = 'intraday_stream'
TICKER_METADATA_TABLE_NAME = 'tickers'
ANALYSIS_REPORTS_TABLE_NAME = 'backtest_reports'