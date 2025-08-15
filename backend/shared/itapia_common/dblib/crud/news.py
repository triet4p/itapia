# common/dblib/crud/news.py
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

def get_relevant_news(rdbms_session: Session, table_name: str, ticker: str, skip: int = 0, limit: int = 10):
    query = text(f"""
        SELECT news_uuid, ticker, title, summary, provider, link, publish_time, collect_time
        FROM {table_name} 
        WHERE ticker = :ticker 
        ORDER BY publish_time DESC, collect_time DESC 
        OFFSET :skip LIMIT :limit
    """)
    result = rdbms_session.execute(query, {"ticker": ticker, "skip": skip, "limit": limit})
    return result.mappings().all()

def get_universal_news(rdbms_session: Session, table_name: str, search_terms: str, skip: int = 0, limit: int = 10):
    query = text(f"""
        SELECT 
            news_uuid, keyword, title, summary, provider, link, 
            publish_time, collect_time, title_hash,
            ts_rank(keyword_tsv, plainto_tsquery('english', :search_query)) AS rank
        FROM 
            {table_name}
        WHERE 
            keyword_tsv @@ plainto_tsquery('english', :search_query)
        ORDER BY 
            rank DESC, news_prior DESC, publish_time DESC, collect_time DESC
        OFFSET :skip 
        LIMIT :limit
    """)
    result = rdbms_session.execute(query, {"search_query": search_terms, "skip": skip, "limit": limit})
    return result.mappings().all()

def get_universal_news_with_date(rdbms_session: Session, table_name: str, search_terms: str, 
                                 before_date: datetime,
                                 skip: int = 0, limit: int = 10):
    query = text(f"""
        SELECT 
            news_uuid, keyword, title, summary, provider, link, 
            publish_time, collect_time, title_hash,
            ts_rank(keyword_tsv, plainto_tsquery('english', :search_query)) AS rank
        FROM 
            {table_name}
        WHERE 
            keyword_tsv @@ plainto_tsquery('english', :search_query) AND publish_time <= :before_date
        ORDER BY 
            rank DESC, news_prior DESC, publish_time DESC, collect_time DESC
        OFFSET :skip 
        LIMIT :limit
    """)
    result = rdbms_session.execute(query, {"search_query": search_terms, "skip": skip, "limit": limit,
                                           'before_date': before_date})
    return result.mappings().all()