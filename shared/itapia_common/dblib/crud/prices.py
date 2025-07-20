# common/dblib/crud/prices.py

# app/crud/prices.py

from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import text, Engine

from redis.client import Redis

def get_daily_prices(rdbms_session: Session, table_name: str, ticker: str, skip: int = 0, limit: int = 500):
    query = text(f"""
        SELECT * FROM {table_name} 
        WHERE ticker = :ticker 
        ORDER BY collect_date DESC 
        OFFSET :skip LIMIT :limit
    """)
    
    result = rdbms_session.execute(query, {"ticker": ticker, "skip": skip, "limit": limit})
    return result.mappings().all()

def get_tickers_by_sector(rdbms_session: Session, table_name: str, sector_code: str):
    query = text(f"""
        SELECT ticker_sym FROM {table_name}
        WHERE sector_code = :sector_code AND is_active = TRUE
        ORDER BY ticker_sym;
    """)
    result = rdbms_session.execute(query, {"sector_code": sector_code})
    # .scalars().all() sẽ trả về một list các giá trị từ cột đầu tiên
    return result.scalars().all()

def get_intraday_prices(redis_client: Redis, ticker: str, stream_prefix: str):
    if not redis_client:
        return None
    redis_key = f'{stream_prefix}:{ticker}'
    entries = redis_client.xrange(redis_key)
    data_lst = []
    if entries:
        for entry_id, data in entries:
            for key, value in data.items():
                if key in ['open', 'high', 'low', 'close']:
                    data[key] = float(value)
                elif key == 'volume':
                    data[key] = int(value)
                elif key == 'last_update_utc':
                    data[key] = datetime.fromisoformat(data[key])
            data['ticker'] = ticker
            data_lst.append(data)
        return data_lst
    else:
        return []

def get_latest_intraday_price(redis_client: Redis, ticker: str, stream_prefix: str):
    if not redis_client:
        return None
    redis_key = f'{stream_prefix}:{ticker}'
    entries = redis_client.xrevrange(redis_key, count=1)
    if not entries:
        return None
    entry_id, data = entries[0]
    for key, value in data.items():
        if key in ['open', 'high', 'low', 'close']:
            data[key] = float(value)
        elif key == 'volume':
            data[key] = int(value)
        elif key == 'last_update_utc':
            data[key] = datetime.fromisoformat(data[key])
    data['ticker'] = ticker

    return data

def get_last_history_date(engine: Engine,
                          table_name: str, 
                          tickers: list[str],
                          default_return_date: datetime):
    query = f"SELECT MAX(collect_date) FROM {table_name} WHERE ticker IN :tickers;"
    stmt = text(query)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(stmt, {"tickers": tuple(tickers)}).scalar()
            if result:
                # Chuyển đổi từ date của DB sang datetime của Python
                return datetime.combine(result, datetime.min.time()).replace(tzinfo=timezone.utc)
            return default_return_date # Trả về None nếu bảng trống
    except Exception as e:
        # Nếu có lỗi (ví dụ bảng chưa tồn tại), coi như chưa có dữ liệu
        return default_return_date
    
def add_intraday_candle(redis_client: Redis, ticker: str, candle_data: dict,
                        stream_prefix: str, max_entries: int = 300):
    """Thêm một cây nến intraday vào một Redis Stream tương ứng với ticker.

    Sử dụng cấu trúc dữ liệu Stream của Redis để lưu trữ hiệu quả chuỗi
    thời gian. Stream sẽ được tự động giới hạn kích thước để tránh
    tiêu thụ quá nhiều bộ nhớ.

    Args:
        ticker (str): Mã cổ phiếu để xác định tên của stream
            (ví dụ: "intraday_stream:AAPL").
        candle_data (dict): Dictionary chứa dữ liệu OHLCV và các thông tin khác
            của cây nến.
        max_entries (int, optional): Số lượng entry tối đa cần giữ lại
            trong stream. Mặc định là 300.
    """
    if not candle_data:
        return
    stream_key = f"{stream_prefix}:{ticker}"
    
    try:
        # Chuyển đổi tất cả giá trị sang string để tương thích với Redis Stream
        mapping_to_save = {k: str(v) for k, v in candle_data.items()}

        # Lệnh XADD để thêm entry mới. '*' để Redis tự tạo ID dựa trên timestamp.
        # MAXLEN ~ max_entries giới hạn kích thước của stream.
        redis_client.xadd(stream_key, mapping_to_save, maxlen=max_entries, approximate=True)
        
        # Không cần đặt TTL nữa vì stream sẽ tự cắt bớt dữ liệu cũ.
        # Dữ liệu sẽ tự động được thay thế vào ngày hôm sau.

    except Exception as e:
        raise