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
    """Thực hiện thu thập dữ liệu tin tức của một list các cổ phiếu trong một khung thời gian"""
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
    transformed = {}
    
    # Sử dụng uuid.uuid4() làm fallback nếu 'id' không tồn tại
    transformed['news_uuid'] = element.get('id')
    if transformed['news_uuid'] is None:
        transformed['news_uuid'] = str(uuid.uuid4())
        logger.warn('Use UUID generate alternative!')
    
    content = element.get('content')
    if not content: # Kiểm tra cả None và dictionary rỗng
        raise FetchException(f"News with id {transformed['news_uuid']} do not have 'content'")
    
    # Lấy các giá trị đơn giản
    transformed['title'] = content.get('title')
    if not transformed['title']: # Tiêu đề là bắt buộc
        raise FetchException(f"News with id {transformed['news_uuid']} do not have 'title'")

    transformed['summary'] = content.get('summary', '') # Mặc định là chuỗi rỗng nếu thiếu
    
    # Xử lý thời gian một cách an toàn
    pub_date_str = content.get('pubDate')
    if pub_date_str:
        # yfinance trả về timestamp (int), cần chuyển đổi
        transformed['publish_time'] = datetime.fromisoformat(pub_date_str)
    else:
        # Nếu không có ngày xuất bản, chúng ta không thể sử dụng tin này
        raise FetchException(f"News with id {transformed['news_uuid']} do not have 'pubDate'")

    transformed['collect_time'] = datetime.now(timezone.utc)

    # Lấy 'provider' một cách an toàn
    provider_info = content.get('provider') # Có thể là dict hoặc None
    transformed['provider'] = provider_info.get('displayName', '') if provider_info else ''

    # Lấy 'link' một cách an toàn
    click_through_info = content.get('clickThroughUrl') # Có thể là dict hoặc None
    transformed['link'] = click_through_info.get('url', '') if click_through_info else ''
    
    # Lấy 'ticker' từ một cấp cao hơn nếu có
    transformed['ticker'] = element['ticker']

    return transformed

def _transform(data: list[dict]):
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
    """Thực thi pipeline hoàn chỉnh để thu thập tin tức liên quan đến các cổ phiếu.

    Quy trình bao gồm:
    1. Lấy danh sách tất cả các ticker đang hoạt động từ DB manager.
    2. Lặp qua từng ticker, gọi API của yfinance để lấy tin tức.
    3. Chuyển đổi và chuẩn hóa dữ liệu tin tức thô.
    4. Ghi các tin tức mới vào cơ sở dữ liệu, bỏ qua nếu đã tồn tại.

    Args:
        table_name (str): Tên bảng trong CSDL để lưu dữ liệu (ví dụ: 'relevant_news').
        max_news (int, optional): Số lượng tin tức tối đa lấy cho mỗi ticker. Mặc định là 10.
        sleep_time (int, optional): Thời gian nghỉ (giây) giữa các request API. Mặc định là 5.
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