# app/db/session.py
"""
Quản lý việc tạo và cung cấp các session kết nối đến cơ sở dữ liệu.

Module này chịu trách nhiệm khởi tạo SQLAlchemy engine và Redis client.
Nó cung cấp các hàm "dependency" cho FastAPI để "tiêm" các session này
vào các endpoint một cách hiệu quả và an toàn, đảm bảo mỗi request
sẽ có một session riêng và sẽ được đóng lại sau khi hoàn thành.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import redis
from redis.client import Redis

from app.core.config import DATABASE_URL, REDIS_HOST, REDIS_PORT

from app.logger import *

# --- PostgreSQL Setup ---
info('Setting SQL DB ...')
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency để "tiêm" session DB vào các endpoint
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Redis Setup ---
info('Setting Redis Client ...')
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True
)

# Dependency để "tiêm" kết nối Redis
def get_redis() -> Generator[Redis | None, None, None]:
    try:
        # Kiểm tra kết nối trước khi trả về
        redis_client.ping()
        yield redis_client
    except redis.exceptions.ConnectionError as e:
        # Trả về None hoặc ném ra một lỗi HTTP 503 Service Unavailable
        yield None