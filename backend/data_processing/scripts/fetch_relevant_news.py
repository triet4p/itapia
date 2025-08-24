"""Stock news fetching and processing pipeline.

This module implements a pipeline to fetch relevant stock news
from Yahoo Finance, process the data, and store it in the database.
"""

from datetime import datetime, timezone
import time

import uuid

import yfinance as yf

from .utils import FetchException

from itapia_common.dblib.session import get_singleton_rdbms_engine
from itapia_common.dblib.services import DataMetadataService, DataNewsService
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Relevant news Processor')

def _extract_news_data(tickers: list[str],
                       sleep_time: int = 5,
                       max_news: int = 10) -> list[dict]:
    """Extract news data for a list of stock tickers.

    Args:
        tickers (list[str]): List of stock ticker symbols to fetch news for.
        sleep_time (int, optional): Time to wait (in seconds) between requests. Defaults to 5.
        max_news (int, optional): Maximum number of news items per ticker. Defaults to 10.

    Returns:
        list[dict]: List of raw news data dictionaries.
    """
    data = []
    for ticker in tickers:
        new_data = yf.Ticker(ticker).get_news(max_news, 'news')
        
        for element in new_data:
            element['ticker'] = ticker
        
        time.sleep(sleep_time)
        
        if len(new_data) == 0:
            continue
        data.extend(new_data)        
        
    return data

def _transform_element(element: dict):
    """Transform a single news element into the database schema.

    Args:
        element (dict): Raw news data from Yahoo Finance.

    Returns:
        dict: Transformed news data compatible with database schema.

    Raises:
        FetchException: If required fields are missing from the news data.
    """
    transformed = {}
    
    # Use uuid.uuid4() as fallback if 'id' doesn't exist
    transformed['news_uuid'] = element.get('id')
    if transformed['news_uuid'] is None:
        transformed['news_uuid'] = str(uuid.uuid4())
        logger.warn('Use UUID generate alternative!')
    
    content = element.get('content')
    if not content: # Check for both None and empty dictionary
        raise FetchException(f"News with id {transformed['news_uuid']} do not have 'content'")
    
    # Get simple values
    transformed['title'] = content.get('title')
    if not transformed['title']: # Title is required
        raise FetchException(f"News with id {transformed['news_uuid']} do not have 'title'")

    transformed['summary'] = content.get('summary', '') # Default to empty string if missing
    
    # Safely process time
    pub_date_str = content.get('pubDate')
    if pub_date_str:
        # yfinance returns timestamp (int), needs conversion
        transformed['publish_time'] = datetime.fromisoformat(pub_date_str)
    else:
        # If no publication date, we can't use this news
        raise FetchException(f"News with id {transformed['news_uuid']} do not have 'pubDate'")

    transformed['collect_time'] = datetime.now(timezone.utc)

    # Safely get 'provider'
    provider_info = content.get('provider') # Could be dict or None
    transformed['provider'] = provider_info.get('displayName', '') if provider_info else ''

    # Safely get 'link'
    click_through_info = content.get('clickThroughUrl') # Could be dict or None
    transformed['link'] = click_through_info.get('url', '') if click_through_info else ''
    
    # Get 'ticker' from a higher level if available
    transformed['ticker'] = element['ticker']

    return transformed

def _transform(data: list[dict]):
    """Transform raw news data into database schema.

    Args:
        data (list[dict]): List of raw news data dictionaries.

    Returns:
        list[dict]: List of transformed news data dictionaries.
    """
    transformed_data = []
    for element in data:
        try:
            transformed_data.append(_transform_element(element))
        except FetchException as e:
            print(e.msg)
            continue
    return transformed_data

def full_pipeline(metadata_service: DataMetadataService,
                  news_service: DataNewsService,
                  max_news: int = 10,
                  sleep_time: int = 5):
    """Execute complete pipeline to fetch stock-relevant news.

    Process:
    1. Get list of all active tickers from database.
    2. Iterate through each ticker, call yfinance API to get news.
    3. Transform and normalize raw news data.
    4. Write new news to database, skipping if already exists.

    Args:
        metadata_service (DataMetadataService): Service to access ticker metadata.
        news_service (DataNewsService): Service to manage news data storage.
        max_news (int, optional): Maximum number of news items per ticker. Defaults to 10.
        sleep_time (int, optional): Time to wait (in seconds) between API requests. Defaults to 5.
    """
    
    try:
        engine = get_singleton_rdbms_engine()
        tickers = metadata_service.get_all_tickers()
        logger.info(f'Successfully get {len(tickers)} to collect news...')
        logger.info(f'Getting news for {len(tickers)} tickers...')
        data = _extract_news_data(tickers, sleep_time, max_news)
        
        logger.info(f'Transforming news data ...')
        transformed_data = _transform(data)
        
        logger.info(f'Loading news to DB ...')
        news_service.add_news(
            transformed_data, 
            'relevant',
            unique_cols=['news_uuid'],
        )
        
        logger.info(f"Successfully load!")
    except FetchException as e:
        logger.err(f"A fetch exception occured: {e}")
    except Exception as e:
        logger.err(f"An unknown exception occured: {e}")

if __name__ == '__main__':
    
    engine = get_singleton_rdbms_engine()
    metadata_service = DataMetadataService(engine)
    news_service = DataNewsService(engine)
    
    full_pipeline(metadata_service, news_service, 
                  max_news=15, sleep_time=5)