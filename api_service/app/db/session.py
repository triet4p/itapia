from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import redis
from redis.client import Redis

from app.core.config import DATABASE_URL, REDIS_HOST, REDIS_PORT

# --- PostgreSQL Setup ---
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
        print(f"Lỗi kết nối Redis: {e}")
        # Trả về None hoặc ném ra một lỗi HTTP 503 Service Unavailable
        yield None