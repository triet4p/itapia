import sys
from typing import Literal
import yfinance as yf
import time
from datetime import datetime, timezone
import uuid

from utils import TO_FETCH_TICKERS_BY_REGION, FetchException
from db_manager import PostgreDBManager

def _extract_news_data(tickers: list[str],
                       sleep_time: int = 5,
                       max_news: int = 10) -> list[dict]:
    data = []
    for ticker in tickers:
        new_data = yf.Ticker(ticker).get_news(max_news, 'news')
        print(f'Successfully get {len(new_data)} for ticker {ticker}')
        
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
    transformed['news_uuid'] = element.get('id') or str(uuid.uuid4())
    
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

def full_pipeline(table_name: str,
                  db_mng: PostgreDBManager,
                  max_news: int = 10,
                  sleep_time: int = 5):
    """
    Pipeline lấy dữ liệu tin tức của các cổ phiếu thuộc 1 region được chỉ định
    rồi xử lý giá trị thiếu và lưu vào Postgre SQL.

    Args:
        region (Literal[&#39;americas&#39;, &#39;europe&#39;, &#39;asia_pacific&#39;]): Khu vực được hỗ trợ.
            Dữ liệu thường phải lấy theo khu vực vì timezone khác nhau.
        table_name (str): Tên bảng được lưu trong CSDL
        db_manager (PostgreDBManager): Quản lý truy cập CSDL
        max_news (int): Số lượng tin tức nhiều nhất lấy từ mỗi cổ phiếu. Defaults to 10.
        sleep_time (int): Thời gian chờ giữa mỗi request để tránh time limit. Defaults to 5.
    """
    tickers = list(db_mng.get_active_tickers_with_info().keys())
    try:
        print(f'Get news for {len(tickers)} tickers.')
        data = _extract_news_data(tickers, sleep_time, max_news)
        transformed_data = _transform(data)
        
        db_mng.bulk_insert(
            table_name, 
            transformed_data, 
            unique_cols=['news_uuid'],
            chunk_size=300,
            on_conflict='nothing'
        )
        
        print(f"Successfully!")
    except FetchException as e:
        print(f"A fetch exception occured: {e}")
    except Exception as e:
        print(f"An unknown exception occured: {e}")

if __name__ == '__main__':
    
    TABLE_NAME = 'relevant_news'
    
    db_mng = PostgreDBManager()
    
    full_pipeline(table_name=TABLE_NAME, db_mng=db_mng,
                  max_news=15, sleep_time=5)