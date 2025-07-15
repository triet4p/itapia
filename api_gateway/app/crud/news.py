# app/crud/news.py

from sqlalchemy.orm import Session
from sqlalchemy import text

def get_news(db: Session, ticker: str, skip: int = 0, limit: int = 10):
    query = text("""
        SELECT news_uuid, ticker, title, summary, provider, link, publish_time, collect_time
        FROM relevant_news 
        WHERE ticker = :ticker 
        ORDER BY publish_time, collect_time DESC 
        OFFSET :skip LIMIT :limit
    """)
    result = db.execute(query, {"ticker": ticker, "skip": skip, "limit": limit})
    return result.mappings().all()