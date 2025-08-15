from datetime import datetime
from typing import List, Literal

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from itapia_common.dblib.crud.news import get_relevant_news, get_universal_news, get_universal_news_with_date
from itapia_common.dblib.crud.general_update import bulk_insert
from itapia_common.schemas.entities.news import RelevantNews, RelevantNewsPoint,\
    UniversalNews, UniversalNewsPoint

from .metadata import APIMetadataService

import itapia_common.dblib.db_config as dbcfg

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('News Service of DB')

class APINewsService:
    def __init__(self, rdbms_session: Session,
                 metadata_service: APIMetadataService):
        self.rdbms_session = rdbms_session
        self.metadata_service = metadata_service
        
    def get_relevant_news(self, ticker: str, skip: int, limit: int) -> RelevantNews:
        """Lấy và đóng gói dữ liệu tin tức cho một ticker."""
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
        """Lấy và đóng gói dữ liệu tin tức cho một ticker."""
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
    def __init__(self, engine: Engine):
        self.engine = engine
        
    def add_news(self, data: list[dict],
                 type: Literal['relevant', 'universal'],
                 unique_cols: list[str]):
        if type == 'relevant':
            table_name = dbcfg.RELEVANT_NEWS_TABLE_NAME
        else:
            table_name = dbcfg.UNIVERSAL_NEWS_TABLE_NAME
        bulk_insert(self.engine, table_name, data, unique_cols,
                    chunk_size=150, on_conflict='nothing')
        
    