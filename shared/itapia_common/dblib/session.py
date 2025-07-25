# common/dblib/session.py
from typing import Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

import redis
from redis.client import Redis
import redis.exceptions

import itapia_common.dblib.db_config as cfg

_SINGLETON_RDBMS_ENGINE = None
_SINGLETON_REDIS_CLIENT = None

def get_singleton_rdbms_engine() -> Engine:
    global _SINGLETON_RDBMS_ENGINE
    if _SINGLETON_RDBMS_ENGINE is None:
        _SINGLETON_RDBMS_ENGINE = create_engine(cfg.DATABASE_URL, pool_pre_ping=True)
    return _SINGLETON_RDBMS_ENGINE

def get_singleton_redis_client() -> Redis:
    global _SINGLETON_REDIS_CLIENT
    if _SINGLETON_REDIS_CLIENT is None:
        try:
            _SINGLETON_REDIS_CLIENT = redis.Redis(
                host=cfg.REDIS_HOST, port=cfg.REDIS_PORT, db=0,
                decode_responses=True
            )
            _SINGLETON_REDIS_CLIENT.ping()
        except redis.exceptions.ConnectionError:
            raise
    return _SINGLETON_REDIS_CLIENT

def get_rdbms_session() -> Generator[Session, None, None]:
    """
    Dependency cho FastAPI: Mở một session DB mới cho mỗi request.
    """
    engine = get_singleton_rdbms_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    rdbms_session = SessionLocal()
    try:
        yield rdbms_session
    finally:
        rdbms_session.close()
        
def get_redis_connection() -> Generator[Redis | None, None, None]:
    """
    Dependency cho FastAPI: Cung cấp Redis client đã được khởi tạo.
    """
    # Chỉ cần yield client đã được khởi tạo theo kiểu singleton
    yield get_singleton_redis_client()       