import requests
from typing import Dict, List

from app.core.config import GATEWAY_HTTP_BASE_URL

from app.logger import *

def _make_request(endpoint: str, params: Dict = None):
    url = f'{GATEWAY_HTTP_BASE_URL}{endpoint}'
    info(f"Data Accessor: Getting data from url {url}")
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status() # Ném lỗi cho các status code 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        err(f"Data Accessor: Error fetching data from {url}: {e}")
        # Trả về None hoặc một cấu trúc lỗi chuẩn thay vì ném ValueError
        # để orchestrator có thể xử lý một cách duyên dáng.
        return None
    
def fetch_daily_prices_for_ticker(ticker: str, skip: int = 0, limit: int = 2000) -> Dict | None:
    """Lấy dữ liệu giá hàng ngày cho một ticker."""
    return _make_request(f"/prices/daily/{ticker.upper()}", params={'skip': skip, 'limit': limit})

def fetch_intraday_prices_for_ticker(ticker: str) -> Dict | None:
    """Lấy toàn bộ dữ liệu giá trong ngày cho một ticker."""
    return _make_request(f"/prices/intraday/history/{ticker.upper()}")

def fetch_news_for_ticker(ticker: str, skip: int = 0, limit: int = 100) -> Dict | None:
    """Lấy tin tức cho một ticker."""
    return _make_request(f"/news/{ticker.upper()}", params={'skip': skip, 'limit': limit})

def fetch_daily_prices_for_sector(sector_code: str, skip: int = 0, limit: int = 2000) -> List[Dict] | None:
    """Lấy dữ liệu giá hàng ngày cho cả một nhóm ngành."""
    return _make_request(f"/prices/sector/daily/{sector_code.upper()}", params={'skip': skip, 'limit': limit})

def fetch_all_sectors() -> List[Dict] | None:
    """Lấy danh sách tất cả các nhóm ngành."""
    return _make_request("/metadata/sectors")