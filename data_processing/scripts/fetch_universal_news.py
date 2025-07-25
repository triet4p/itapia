# data_processing/scripts/fetch_universal_news.py

from datetime import datetime, timezone, timedelta
import hashlib
import re
import time
from urllib.parse import urlparse, urlunparse
import uuid
from gnews import GNews

from utils import FetchException, UNIVERSAL_KEYWORDS_EN, UNIVERSAL_TOPIC_EN

from itapia_common.dblib.session import get_singleton_rdbms_engine
from itapia_common.dblib.services import DataNewsService
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Universal News Processor')

def _extract_news_data_by_keyword(keywords: list[str],
                       period_days: int = 5,
                       sleep_time: int = 5,
                       max_results: int = 20) -> list[dict]:
    """Thực hiện thu thập dữ liệu tin tức cho một list các từ khóa."""
    all_news_data = []
    gnews_client = GNews(language='en', country='US', max_results=max_results, period=f'{period_days}d')
    
    for keyword in keywords:
        logger.info(f"Fetching news for keyword: '{keyword}'...")
        try:
            news_for_keyword = gnews_client.get_news(keyword)
            
            # Gắn từ khóa vào mỗi bản tin để biết nguồn gốc
            for article in news_for_keyword:
                article['keyword'] = keyword
                article['prior'] = 2
            
            all_news_data.extend(news_for_keyword)
            
        except Exception as e:
            logger.err(f"Failed to fetch news for '{keyword}'. Error: {e}")
        
        # Luôn có độ trễ để tránh bị chặn
        time.sleep(sleep_time)
        
    return all_news_data

def _extract_news_data_by_topic(topics: list[str],
                       period_days: int = 5,
                       sleep_time: int = 5,
                       max_results: int = 20) -> list[dict]:
    """Thực hiện thu thập dữ liệu tin tức cho một list các từ khóa."""
    all_news_data = []
    gnews_client = GNews(language='en', country='US', max_results=max_results, period=f'{period_days}d')
    
    for topic in topics:
        logger.info(f"Fetching news for topic: '{topic}'...")
        try:
            news_for_keyword = gnews_client.get_news(topic)
            
            # Gắn từ khóa vào mỗi bản tin để biết nguồn gốc
            for article in news_for_keyword:
                article['keyword'] = topic
                article['prior'] = 1
            
            all_news_data.extend(news_for_keyword)
            
        except Exception as e:
            logger.err(f"Failed to fetch news for '{topic}'. Error: {e}")
        
        # Luôn có độ trễ để tránh bị chặn
        time.sleep(sleep_time)
        
    return all_news_data

def _normalize_text(text: str) -> str:
    """Chuẩn hóa văn bản để tạo định danh nhất quán."""
    if not text:
        return ""
    # Chuyển về chữ thường
    text = text.lower()
    # Loại bỏ dấu câu
    text = re.sub(r'[^\w\s]', '', text)
    # Loại bỏ khoảng trắng thừa
    text = " ".join(text.split())
    return text

def _normalize_url(url: str) -> str:
    """Chuẩn hóa URL để loại bỏ các yếu tố không cần thiết."""
    if not url:
        return ""
    parsed = urlparse(url)
    # Xây dựng lại URL chỉ với các thành phần cốt lõi, bỏ qua query params, fragment
    # Có thể tùy chỉnh để giữ lại một số query params quan trọng nếu cần
    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    # Đảm bảo có trailing slash hoặc không có để nhất quán
    return clean_url.lower()

def _generate_article_uuid(link: str, title: str) -> str:
    """
    Tạo UUID v5 duy nhất và nhất quán cho một phiên bản bài báo cụ thể
    dựa trên link và title đã được chuẩn hóa.
    """
    normalized_link = _normalize_url(link)
    normalized_title = _normalize_text(title)
    
    # Sử dụng một ký tự phân tách rõ ràng để tránh va chạm
    # Ví dụ: link='ab', title='c' và link='a', title='bc' đều tạo ra 'abc'
    # 'ab|c' và 'a|bc' sẽ khác nhau.
    canonical_string = f"{normalized_link}|{normalized_title}"
    
    return str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_string))

def _create_content_hash(text: str) -> str:
    """Tạo một hash SHA-256 từ văn bản đã được chuẩn hóa."""
    normalized = _normalize_text(text)
    # Dùng SHA-256 để có độ an toàn cao và gần như không thể trùng lặp
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def _transform_element(element: dict):
    """Chuyển đổi một dictionary tin tức từ gnews sang schema CSDL."""
    transformed = {}
    
    # GNews không có UUID sẵn, chúng ta sẽ tạo dựa trên link hoặc uuid4
    # Sử dụng link làm base để tạo UUID ổn định hơn, tránh trùng lặp
    link = element.get('url')
    title = element.get('title')
    if (not link) or (not title):
        raise FetchException("News article is missing 'url', cannot create a stable UUID.")
        
    transformed['news_uuid'] = _generate_article_uuid(link, title)
    
    transformed['title'] = title
    if not transformed['title']:
        raise FetchException(f"News with link {link} is missing a 'title'.")
    
    transformed['title_hash'] = _create_content_hash(title)

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
    transformed['news_prior'] = element['prior']

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
                  topics: list[str],
                  period_days: int = 5,
                  max_results: int = 20,
                  sleep_time: int = 5):
    """
    Thực thi pipeline hoàn chỉnh để thu thập tin tức universal.
    """
    try:
        logger.info(f'Getting universal news for {len(keywords)} keywords...')
        raw_data1 = _extract_news_data_by_keyword(keywords, period_days, sleep_time, max_results)
        
        logger.info(f'Getting universal news for {len(topics)} topics...')
        raw_data2 = _extract_news_data_by_topic(topics, period_days, sleep_time, max_results)
        
        raw_data = raw_data1 + raw_data2
        
        logger.info(f'Transforming {len(raw_data)} news articles...')
        transformed_data = _transform(raw_data)
        
        logger.info(f'Loading {len(transformed_data)} news articles to DB...')
        news_service.add_news(
            data=transformed_data, 
            type='universal',
            unique_cols=['title_hash']
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
        topics=UNIVERSAL_TOPIC_EN,
        period_days=7,
        max_results=15, 
        sleep_time=4
    )