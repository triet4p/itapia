"""Service layer for news-related operations.

This module provides high-level interfaces for retrieving and managing news data,
handling conversion between raw database records and Pydantic models.
"""

from datetime import datetime
from typing import List, Literal, Optional

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from itapia_common.dblib.crud.news import get_relevant_news, get_universal_news, get_universal_news_with_date
from itapia_common.dblib.crud.general_update import bulk_insert
from itapia_common.schemas.entities.news import RelevantNews, RelevantNewsPoint,    UniversalNews, UniversalNewsPoint

from .metadata import APIMetadataService

import itapia_common.dblib.db_config as dbcfg

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('News Service of DB')

class APINewsService:
    """Service class for API-level news operations."""
    
    def __init__(self, rdbms_session: Optional[Session],
                 metadata_service: APIMetadataService):
        self.rdbms_session: Session = None
        self.metadata_service = metadata_service
        if rdbms_session is not None:
            self.set_rdbms_session(rdbms_session)
        
    def set_rdbms_session(self, rdbms_session: Session):
        self.rdbms_session = rdbms_session
        
    def get_relevant_news(self, ticker: str, skip: int, limit: int) -> RelevantNews:
        """Retrieve and package news data for a specific ticker.

        This method fetches relevant news articles for a ticker and converts them
        to Pydantic models with proper timestamp handling.

        Args:
            ticker (str): The ticker symbol to retrieve news for.
            skip (int): Number of records to skip for pagination.
            limit (int): Maximum number of records to return.

        Returns:
            RelevantNews: A packaged news response with metadata and data points.
        """
        if self.rdbms_session is None:
            raise ValueError('Connection is empty!!')
        logger.info(f"SERVICE: Preparing news data for ticker {ticker}")
        metadata = self.metadata_service.get_validate_ticker_info(ticker, data_type='news')
        
        news_rows = get_relevant_news(self.rdbms_session, dbcfg.RELEVANT_NEWS_TABLE_NAME, 
                                      ticker, skip=skip, limit=limit)
        
        news_points = [
            RelevantNewsPoint(
                collect_ts=int(row['collect_time'].timestamp()),
                publish_ts=int(row['publish_time'].timestamp()) if row['publish_time'] else None,
                **row
            ) for row in news_rows
        ]
        
        return RelevantNews(metadata=metadata,
                                       datas=news_points) 
        
    def get_universal_news(self, search_terms: str, skip: int, limit: int,
                           before_date: datetime|None = None) -> UniversalNews:
        """Retrieve and package universal news data based on search terms.

        This method searches for news articles across all tickers and converts them
        to Pydantic models with proper timestamp handling.

        Args:
            search_terms (str): Search terms to match against news articles.
            skip (int): Number of records to skip for pagination.
            limit (int): Maximum number of records to return.
            before_date (datetime | None, optional): Maximum date for filtering news articles.

        Returns:
            UniversalNews: A packaged news response with data points.
        """
        if self.rdbms_session is None:
            raise ValueError('Connection is empty!!')
        logger.info(f"SERVICE: Preparing {limit} universal news ...")
        
        if before_date is None:
            news_rows = get_universal_news(self.rdbms_session, dbcfg.UNIVERSAL_NEWS_TABLE_NAME,
                                        search_terms=search_terms,
                                        skip=skip, limit=limit)
        
        else:
            news_rows = get_universal_news_with_date(self.rdbms_session, dbcfg.UNIVERSAL_NEWS_TABLE_NAME,
                                        search_terms=search_terms,
                                        before_date=before_date,
                                        skip=skip, limit=limit)
        
        news_points = [
            UniversalNewsPoint(
                collect_ts=int(row['collect_time'].timestamp()),
                publish_ts=int(row['publish_time'].timestamp()) if row['publish_time'] else None,
                **row
            ) for row in news_rows
        ]
        
        return UniversalNews(datas=news_points) 
    
class DataNewsService:
    """Service class for data-level news operations."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        
    def add_news(self, data: list[dict],
                 type: Literal['relevant', 'universal'],
                 unique_cols: list[str]):
        """Add news articles to the database.

        Args:
            data (list[dict]): List of news article data to insert.
            type (Literal['relevant', 'universal']): Type of news articles.
            unique_cols (list[str]): List of columns that make up a unique constraint.
        """
        if type == 'relevant':
            table_name = dbcfg.RELEVANT_NEWS_TABLE_NAME
        else:
            table_name = dbcfg.UNIVERSAL_NEWS_TABLE_NAME
        bulk_insert(self.engine, table_name, data, unique_cols,
                    chunk_size=150, on_conflict='nothing')