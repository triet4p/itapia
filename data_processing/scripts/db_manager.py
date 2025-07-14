from pathlib import Path
from dotenv import load_dotenv
import os
from typing import Literal

from datetime import datetime, timedelta, timezone
import pandas as pd

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.schema import Table, MetaData
from sqlalchemy.dialects.postgresql import insert as pg_insert

import redis
import redis.exceptions
from redis.client import Redis

from utils import FetchException, DEFAULT_START_DATE

from logger import *

class PostgreDBManager:
    """
    Quản lý tất cả các tương tác với cơ sở dữ liệu PostgreSQL.

    Lớp này hoạt động theo mẫu Singleton cho engine kết nối và cache metadata
    để đảm bảo hiệu quả và tính nhất quán trong toàn bộ ứng dụng.
    Nó cung cấp các phương thức cấp cao để lấy dữ liệu tĩnh và ghi dữ liệu động.
    """
    def __init__(self):
        self._engine: Engine = None
        self._ticker_info_cache = None
    
    def get_engine(self) -> Engine:
        """
        Khởi tạo và trả về một SQLAlchemy Engine duy nhất để kết nối tới CSDL.

        Sử dụng cơ chế Singleton để đảm bảo chỉ có một engine được tạo ra.
        Đọc thông tin kết nối từ các biến môi trường trong file `.env`.

        Raises:
            FetchException: Khi không tìm thấy file cấu hình hoặc kết nối thất bại.

        Returns:
            Engine: Một instance của SQLAlchemy Engine đã sẵn sàng để sử dụng.
        """
        if self._engine is not None:
            warn("Engine existed.")
            return self._engine
        
        info('Loading ENV from .env file ...')
        env_path = Path(__file__).parent.parent.parent / '.env'
        load_dotenv(env_path)
        
        db_host = os.getenv('POSTGRES_HOST')
        db_port = os.getenv('POSTGRES_PORT')
        db_user = os.getenv('POSTGRES_USER')
        db_password = os.getenv('POSTGRES_PASSWORD')
        db_name = os.getenv('POSTGRES_DB')
        
        db_url = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        
        info('Connecting to DB ...')
        try:
            engine = create_engine(db_url)
            info('Successfully connect')
            return engine
        except Exception as e:
            err_msg = f'Failed connection to {db_url}'
            err(err_msg)
            raise FetchException(err_msg)
        
    def _bulk_insert_on_conflict_do_nothing(self, table_name: str,
                                            data: list[dict],
                                            unique_cols: list[str],
                                            chunk_size: int = 1000):
        
        engine = self.get_engine()
        
        info(f'Inserting data to table {table_name} with ON CONFLICT DO NOTHING ...')
        
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)
        total_processed = 0
        
        with engine.begin() as connection:
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                
                stmt = pg_insert(table).values(chunk)
                final_stmt = stmt.on_conflict_do_nothing(
                    index_elements=unique_cols
                )
                
                connection.execute(final_stmt)
                total_processed += len(chunk)
                info(f"Processed {total_processed}/{len(data)} line...")

        info(f"Succesfully insert {total_processed} lines into '{table_name}'.")

    def _bulk_insert_on_conflict_do_update(self, table_name: str,
                                           data: list[dict],
                                           unique_cols: list[str],
                                           chunk_size: int = 1000):
        engine = self.get_engine()
        
        info(f'Inserting data to table {table_name} with ON CONFLICT DO UPDATE ...')
        
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)
        
        total_inserted = 0
        
        with engine.begin() as connection:
            # Lặp qua dữ liệu theo từng khối (chunk)
            for i in range(0, len(data), chunk_size):
                # Lấy ra một khối dữ liệu nhỏ
                chunk = data[i:i + chunk_size]
                
                # Xây dựng và thực thi câu lệnh UPSERT chỉ cho khối này
                stmt = pg_insert(table).values(chunk)
                update_cols = {col.name: col for col in stmt.excluded if col.name not in unique_cols}
                final_stmt = stmt.on_conflict_do_update(
                    index_elements=unique_cols,
                    set_=update_cols
                )
                
                connection.execute(final_stmt)
                total_inserted += len(chunk)
                info(f"Processed {total_inserted}/{len(data)} line...")

        info(f"Succesfully insert {total_inserted} lines into '{table_name}'.")
        
    def bulk_insert(self, table_name: str, 
                    data: list[dict]|pd.DataFrame,
                    unique_cols: list[str],
                    chunk_size: int = 1000,
                    on_conflict: Literal['nothing', 'update'] = 'nothing'):
        """Ghi hàng loạt bản ghi vào một bảng động với xử lý xung đột (UPSERT).

        Hàm này được tối ưu hóa để ghi dữ liệu vào các bảng có dữ liệu thay đổi
        thường xuyên như 'daily_prices' hoặc 'relevant_news'. Nó thực hiện
        việc ghi theo từng khối (chunk) và trong một transaction duy nhất để
        đảm bảo tính toàn vẹn dữ liệu.

        Args:
            table_name (str): Tên của bảng cần ghi dữ liệu. Phải là một trong
                các bảng động được phép.
            data (list[dict] | pd.DataFrame): Dữ liệu cần ghi, dưới dạng list
                các dictionary hoặc một pandas DataFrame.
            unique_cols (list[str]): Danh sách các cột tạo nên một khóa duy nhất
                để xác định xung đột.
            chunk_size (int, optional): Số lượng bản ghi trong mỗi batch ghi.
                Mặc định là 1000.
            on_conflict (Literal['nothing', 'update'], optional): Hành động cần
                thực hiện khi có xung đột. 'nothing' sẽ bỏ qua bản ghi mới,
                'update' sẽ cập nhật bản ghi cũ. Mặc định là 'nothing'.
        
        Raises:
            ValueError: Nếu `table_name` không phải là bảng động được phép.
        """
    
        # Chuyển đổi về dạng json trước
        if isinstance(data, pd.DataFrame):
            if data.empty:
                print('Data is empty!')
                return
            _data = data.to_dict(orient='records')
        else:
            if not data:
                print('Data is empty!')
                return
            _data = data
        
        # Thực hiện insert
        if on_conflict == 'nothing':
            self._bulk_insert_on_conflict_do_nothing(table_name, _data, unique_cols, chunk_size)
        else:
            self._bulk_insert_on_conflict_do_update(table_name, _data, unique_cols, chunk_size)
    
    def get_last_history_date(self, table_name: str, tickers: list[str]):
        """Lấy ngày gần nhất có dữ liệu lịch sử cho một danh sách các ticker.

        Args:
            table_name (str): Tên bảng chứa dữ liệu lịch sử (ví dụ: 'daily_prices').
            tickers (list[str]): Danh sách các mã ticker cần kiểm tra.

        Returns:
            datetime: Một đối tượng datetime có múi giờ UTC của ngày cuối cùng
                tìm thấy. Trả về một ngày mặc định nếu không có dữ liệu.
        """
        default_return_date = DEFAULT_START_DATE - timedelta(days=1)

        query = f"SELECT MAX(collect_date) FROM {table_name} WHERE ticker IN :tickers;"
        stmt = text(query)
        
        engine = self.get_engine()
        
        try:
            with engine.connect() as connection:
                result = connection.execute(stmt, {"tickers": tuple(tickers)}).scalar()
                if result:
                    # Chuyển đổi từ date của DB sang datetime của Python
                    info('Successfully get last history date.')
                    return datetime.combine(result, datetime.min.time()).replace(tzinfo=timezone.utc)
                warn('No data in DB, return default date.')
                return default_return_date # Trả về None nếu bảng trống
        except Exception as e:
            warn(f"Error when query last history date from db: {e}")
            warn('Return default date')
            # Nếu có lỗi (ví dụ bảng chưa tồn tại), coi như chưa có dữ liệu
            return default_return_date
        
    def _load_ticker_metadata(self):
        """
        Tải thông tin chi tiết của tất cả các ticker đang hoạt động từ DB
        và lưu vào cache trong bộ nhớ.
        Hàm này chỉ nên được gọi một lần.
        """
        info("Loading ticker metadata into cache...")
        query = text("""
            SELECT 
                t.ticker_sym, 
                t.company_name, 
                e.exchange_code, 
                e.currency, 
                e.timezone,
                e.open_time,
                e.close_time,
                s.sector_name
            FROM 
                tickers t
            JOIN 
                exchanges e ON t.exchange_code = e.exchange_code
            JOIN 
                sectors s ON t.sector_code = s.sector_code
            WHERE 
                t.is_active = TRUE;
        """)
        
        engine = self.get_engine()
        with engine.connect() as connection:
            result = connection.execute(query)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            
        # Chuyển DataFrame thành dictionary để tra cứu nhanh
        self._ticker_info_cache = df.set_index('ticker_sym').to_dict('index')
        info(f"Metadata cache loaded with {len(self._ticker_info_cache)} active tickers.")
        
    def get_active_tickers_with_info(self) -> dict[str, dict[str, any]]:
        """Lấy thông tin metadata của tất cả các ticker đang hoạt động.

        Hàm này sử dụng cơ chế cache nội bộ. Trong lần gọi đầu tiên, nó sẽ
        truy vấn database để tải toàn bộ thông tin. Trong các lần gọi tiếp theo,
        nó sẽ trả về ngay lập tức dữ liệu từ cache trong bộ nhớ.

        Returns:
            Dict[str, Dict[str, Any]]: Một dictionary với key là mã ticker và
                value là một dictionary chứa thông tin chi tiết (company_name,
                exchange_code, currency, timezone, etc.).
        """
        if self._ticker_info_cache is None:
            self._load_ticker_metadata()
        return self._ticker_info_cache
    
class RedisManager:
    """Quản lý tất cả các tương tác với Redis server.

    Chịu trách nhiệm khởi tạo kết nối và cung cấp các phương thức để ghi
    dữ liệu real-time, đặc biệt là dữ liệu intraday vào Redis Streams.
    """
    def __init__(self):
        self._connection: Redis = None
        
    def get_connection(self) -> Redis:
        """Khởi tạo và trả về một kết nối Redis duy nhất.

        Sử dụng cơ chế Singleton. Đọc thông tin kết nối từ file `.env`.
        Tự động kiểm tra kết nối bằng lệnh PING.

        Raises:
            redis.exceptions.ConnectionError: Nếu không thể kết nối tới Redis server.

        Returns:
            Redis: Một instance của client Redis đã sẵn sàng để sử dụng.
        """
        if self._connection is not None:
            warn('Connection is existed!')
            return self._connection
        
        info('Loading ENV from .env file ...')
        env_path = Path(__file__).parent.parent.parent / '.env'
        load_dotenv(env_path)
        
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        
        info(f"Connecting to redis {redis_host}:{redis_port}...")
        
        try:
            # decode_responses=True để kết quả trả về là string thay vì bytes
            self._connection = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=0,
                decode_responses=True
            )
            self._connection.ping()
            info("Successfully connect to redis!")
        except redis.exceptions.ConnectionError as e:
            err(f"Error when connect to Redis: {e}")
            raise
        
        return self._connection
        
    def add_intraday_candle(self, ticker: str, candle_data: dict, max_entries: int = 300):
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

        conn = self.get_connection()
        stream_key = f"intraday_stream:{ticker}"
        
        try:
            # Chuyển đổi tất cả giá trị sang string để tương thích với Redis Stream
            mapping_to_save = {k: str(v) for k, v in candle_data.items()}

            # Lệnh XADD để thêm entry mới. '*' để Redis tự tạo ID dựa trên timestamp.
            # MAXLEN ~ max_entries giới hạn kích thước của stream.
            conn.xadd(stream_key, mapping_to_save, maxlen=max_entries, approximate=True)
            
            # Không cần đặt TTL nữa vì stream sẽ tự cắt bớt dữ liệu cũ.
            # Dữ liệu sẽ tự động được thay thế vào ngày hôm sau.

        except Exception as e:
            err(f"Error occured when adding data of {ticker} to Redis Stream: {e}")
            raise