# data_processing/scripts/fetch_universal_news.py

from datetime import datetime, timezone
import time
import uuid
from gnews import GNews

from utils import FetchException, UNIVERSAL_KEYWORDS_EN

from itapia_common.dblib.session import get_singleton_rdbms_engine
from itapia_common.dblib.services import DataNewsService
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Universal News Processor')

def _extract_news_data(keywords: list[str],
                       sleep_time: int = 5,
                       max_results: int = 20) -> list[dict]:
    """Thực hiện thu thập dữ liệu tin tức cho một list các từ khóa."""
    all_news_data = []
    gnews_client = GNews(language='en', country='US', max_results=max_results)
    
    for keyword in keywords:
        logger.info(f"Fetching news for keyword: '{keyword}'...")
        try:
            news_for_keyword = gnews_client.get_news(keyword)
            
            # Gắn từ khóa vào mỗi bản tin để biết nguồn gốc
            for article in news_for_keyword:
                article['keyword'] = keyword
            
            all_news_data.extend(news_for_keyword)
            
        except Exception as e:
            logger.err(f"Failed to fetch news for '{keyword}'. Error: {e}")
        
        # Luôn có độ trễ để tránh bị chặn
        time.sleep(sleep_time)
        
    return all_news_data

def _transform_element(element: dict):
    """Chuyển đổi một dictionary tin tức từ gnews sang schema CSDL."""
    transformed = {}
    
    # GNews không có UUID sẵn, chúng ta sẽ tạo dựa trên link hoặc uuid4
    # Sử dụng link làm base để tạo UUID ổn định hơn, tránh trùng lặp
    link = element.get('url')
    if not link:
        raise FetchException("News article is missing 'url', cannot create a stable UUID.")
        
    transformed['news_uuid'] = str(uuid.uuid5(uuid.NAMESPACE_URL, link))
    
    transformed['title'] = element.get('title')
    if not transformed['title']:
        raise FetchException(f"News with link {link} is missing a 'title'.")

    # GNews không có summary, có thể dùng description
    transformed['summary'] = element.get('description', '')
    
    # Xử lý thời gian
    pub_date_str = element.get('published date')
    if pub_date_str:
        # Format của gnews: 'Tue, 18 Jun 2024 10:00:00 GMT'
        # Chúng ta cần parse nó
        try:
            transformed['publish_time'] = datetime.strptime(
                pub_date_str, '%a, %d %b %Y %H:%M:%S %Z'
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warn(f"Could not parse publish date: {pub_date_str}")
    else:
        logger.warn(f"News with link {link} is missing 'published date'.")

    transformed['collect_time'] = datetime.now(timezone.utc)

    # Lấy thông tin nhà cung cấp
    publisher_info = element.get('publisher') # Đây là dict
    transformed['provider'] = publisher_info.get('title', '') if publisher_info else ''
    transformed['link'] = link
    
    # Thêm từ khóa
    transformed['keyword'] = element['keyword']

    return transformed

def _transform(data: list[dict]):
    transformed_data = []
    for element in data:
        try:
            transformed_data.append(_transform_element(element))
        except FetchException as e:
            logger.warn(e.msg)
            continue
    return transformed_data

def full_pipeline(news_service: DataNewsService,
                  keywords: list[str],
                  max_results: int = 20,
                  sleep_time: int = 5):
    """
    Thực thi pipeline hoàn chỉnh để thu thập tin tức universal.
    """
    try:
        logger.info(f'Getting universal news for {len(keywords)} keywords...')
        raw_data = _extract_news_data(keywords, sleep_time, max_results)
        
        logger.info(f'Transforming {len(raw_data)} news articles...')
        transformed_data = _transform(raw_data)
        
        logger.info(f'Loading {len(transformed_data)} news articles to DB...')
        news_service.add_news(
            data=transformed_data, 
            type='universal',
            unique_cols=['news_uuid']
        )
        
        logger.info(f"Successfully processed universal news!")
    except Exception as e:
        logger.err(f"An unknown exception occurred in the universal news pipeline: {e}")

if __name__ == '__main__':
    
    engine = get_singleton_rdbms_engine()
    news_service = DataNewsService(engine)
    
    full_pipeline(
        news_service=news_service,
        keywords=UNIVERSAL_KEYWORDS_EN,
        max_results=15, 
        sleep_time=4
    )