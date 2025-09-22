# common/dblib/session.py
"""Database session management utilities.

This module provides functions for creating and managing database sessions
and connections for both PostgreSQL and Redis, using singleton patterns
for efficient resource usage.
"""

from typing import Generator

import redis
import redis.exceptions
from redis.client import Redis
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from . import db_config as cfg

_SINGLETON_RDBMS_ENGINE = None
_SINGLETON_REDIS_CLIENT = None


def get_singleton_rdbms_engine() -> Engine:
    """Get or create a singleton database engine instance.

    This function ensures only one database engine is created and reused
    throughout the application lifecycle.

    Returns:
        Engine: A SQLAlchemy database engine instance.
    """
    global _SINGLETON_RDBMS_ENGINE
    if _SINGLETON_RDBMS_ENGINE is None:
        _SINGLETON_RDBMS_ENGINE = create_engine(cfg.DATABASE_URL, pool_pre_ping=True)
    return _SINGLETON_RDBMS_ENGINE


def get_singleton_redis_client() -> Redis:
    """Get or create a singleton Redis client instance.

    This function ensures only one Redis client is created and reused
    throughout the application lifecycle.

    Returns:
        Redis: A Redis client instance.

    Raises:
        redis.exceptions.ConnectionError: If unable to connect to Redis.
    """
    global _SINGLETON_REDIS_CLIENT
    if _SINGLETON_REDIS_CLIENT is None:
        try:
            _SINGLETON_REDIS_CLIENT = redis.Redis(
                host=cfg.REDIS_HOST, port=cfg.REDIS_PORT, db=0, decode_responses=True
            )
            _SINGLETON_REDIS_CLIENT.ping()
        except redis.exceptions.ConnectionError:
            raise
    return _SINGLETON_REDIS_CLIENT


def get_rdbms_session() -> Generator[Session, None, None]:
    """FastAPI dependency: Open a new database session for each request.

    This function creates a database session using the singleton engine
    and ensures proper cleanup after the request is complete.

    Yields:
        Session: A SQLAlchemy database session.
    """
    engine = get_singleton_rdbms_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    rdbms_session = SessionLocal()
    try:
        yield rdbms_session
    finally:
        rdbms_session.close()


def get_redis_connection() -> Generator[Redis | None, None, None]:
    """FastAPI dependency: Provide an initialized Redis client.

    This function yields the singleton Redis client instance.

    Yields:
        Redis | None: A Redis client instance or None if not available.
    """
    # Simply yield the already initialized singleton client
    yield get_singleton_redis_client()
