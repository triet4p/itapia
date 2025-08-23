# common/dblib/crud/news.py
"""Provides CRUD operations for news-related data entities."""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

def get_relevant_news(rdbms_session: Session, table_name: str, ticker: str, skip: int = 0, limit: int = 10) -> list[dict]:
    """Retrieve relevant news articles for a specific ticker.

    This function fetches news articles related to a specific ticker, ordered by 
    publish time and collection time in descending order.

    Args:
        rdbms_session (Session): Database session object.
        table_name (str): Name of the table to query.
        ticker (str): Ticker symbol to filter news articles.
        skip (int, optional): Number of records to skip for pagination. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 10.

    Returns:
        list[dict]: A list of dictionaries containing news article data.
    """
    query = text(f"""
        SELECT news_uuid, ticker, title, summary, provider, link, publish_time, collect_time
        FROM {table_name} 
        WHERE ticker = :ticker 
        ORDER BY publish_time DESC, collect_time DESC 
        OFFSET :skip LIMIT :limit
    """)
    result = rdbms_session.execute(query, {"ticker": ticker, "skip": skip, "limit": limit})
    return result.mappings().all()

def get_universal_news(rdbms_session: Session, table_name: str, search_terms: str, skip: int = 0, limit: int = 10) -> list[dict]:
    """Retrieve universal news articles based on search terms.

    This function searches for news articles across all tickers using full-text search
    capabilities, ranking results by relevance.

    Args:
        rdbms_session (Session): Database session object.
        table_name (str): Name of the table to query.
        search_terms (str): Search terms to match against news articles.
        skip (int, optional): Number of records to skip for pagination. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 10.

    Returns:
        list[dict]: A list of dictionaries containing news article data, ranked by relevance.
    """
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
                                 skip: int = 0, limit: int = 10) -> list[dict]:
    """Retrieve universal news articles based on search terms with a date filter.

    This function searches for news articles across all tickers using full-text search
    capabilities, ranking results by relevance and filtering by a maximum date.

    Args:
        rdbms_session (Session): Database session object.
        table_name (str): Name of the table to query.
        search_terms (str): Search terms to match against news articles.
        before_date (datetime): Maximum date for filtering news articles.
        skip (int, optional): Number of records to skip for pagination. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 10.

    Returns:
        list[dict]: A list of dictionaries containing news article data, ranked by relevance.
    """
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