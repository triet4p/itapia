# common/dblib/crud/news.py
from sqlalchemy.orm import Session
from sqlalchemy import text

def get_relevant_news(rdbms_session: Session, table_name: str, ticker: str, skip: int = 0, limit: int = 10):
    query = text(f"""
        SELECT news_uuid, ticker, title, summary, provider, link, publish_time, collect_time
        FROM {table_name} 
        WHERE ticker = :ticker 
        ORDER BY publish_time, collect_time DESC 
        OFFSET :skip LIMIT :limit
    """)
    result = rdbms_session.execute(query, {"ticker": ticker, "skip": skip, "limit": limit})
    return result.mappings().all()

def get_universal_news(rdbms_session: Session, table_name: str, skip: int = 0, limit: int = 10):
    query = text(f"""
        SELECT news_uuid, keyword, title, summary, provider, link, publish_time, collect_time
        FROM {table_name} 
        ORDER BY publish_time, collect_time DESC 
        OFFSET :skip LIMIT :limit
    """)
    result = rdbms_session.execute(query, {"skip": skip, "limit": limit})
    return result.mappings().all()