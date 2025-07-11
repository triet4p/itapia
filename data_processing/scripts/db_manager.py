from datetime import datetime, timedelta, timezone
import redis.exceptions
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.schema import Table, MetaData
from sqlalchemy.dialects.postgresql import insert as pg_insert

import redis
from redis.client import Redis

from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
from typing import Literal

from utils import TO_FETCH_TICKERS_BY_REGION, FetchException, DEFAULT_START_DATE

class PostgreDBManager:
    def __init__(self):
        self._engine: Engine = None
        self._ticker_info_cache = None
    
    def get_engine(self) -> Engine:
        """
        Lấy một Engine để truy cập và kết nối tới CSDL Postgre.
        Các thông tin về user, password, db name cần được nạp vào file `.env` ở thư mục gốc.

        Raises:
            FetchException: Khi không tìm được file cấu hình hoặc kết nối bị sai

        Returns:
            Engine: Engine giúp kết nối CSDL
        """
        if self._engine is not None:
            return self._engine
        env_path = Path(__file__).parent.parent.parent / '.env'
        load_dotenv(env_path)
        
        db_host = os.getenv('POSTGRES_HOST')
        db_port = os.getenv('POSTGRES_PORT')
        db_user = os.getenv('POSTGRES_USER')
        db_password = os.getenv('POSTGRES_PASSWORD')
        db_name = os.getenv('POSTGRES_DB')
        
        db_url = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        
        try:
            engine = create_engine(db_url)
            print('Successfully connect')
            return engine
        except Exception as e:
            err_msg = f'Failed connection to {db_url}'
            print(err_msg)
            raise FetchException(err_msg)
        
    def _bulk_insert_on_conflict_do_nothing(self, table_name: str,
                                            data: list[dict],
                                            unique_cols: list[str],
                                            chunk_size: int = 1000):
        engine = self.get_engine()
        
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
                print(f"Processed {total_processed}/{len(data)} line...")

        print(f"Succesfully insert {total_processed} lines into '{table_name}'.")

    def _bulk_insert_on_conflict_do_update(self, table_name: str,
                                           data: list[dict],
                                           unique_cols: list[str],
                                           chunk_size: int = 1000):
        engine = self.get_engine()
        
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
                print(f"Processed {total_inserted}/{len(data)} line...")

        print(f"Succesfully insert {total_inserted} lines into '{table_name}'.")
        
    def bulk_insert(self, table_name: str, 
                    data: list[dict]|pd.DataFrame,
                    unique_cols: list[str],
                    chunk_size: int = 1000,
                    on_conflict: Literal['nothing', 'update'] = 'nothing'):
        """
        Hỗ trợ thao tác insert có xử lý duplicate (on conflict) trên 1 loạt bản ghi.
        Các bản ghi sẽ được upsert theo transaction. Nếu 1 bản ghi bị lỗi
        thì cả quá trình sẽ không được ghi nhận

        Args:
            table_name (str): Tên bảng cần upsert
            data (list[dict]|pd.DataFrame): Dữ liệu, là một list các dict, mỗi dict phải gồm các key là tên các cột; 
                hoặc là một DataFrame của pandas chứa các dòng dữ liệu với cột quy định.
            unique_cols (list[str]): Các cột được lấy là điều kiện UNIQUE. Nếu 2 hàng có các dữ liệu trên
                các cột unique này trùng nhau thì sẽ được update.
            chunk_size (int): Số hàng trong 1 batch được chèn vào. Defaults to 1000.
            on_conflict (Literal[&#39;nothing&#39;, &#39;update&#39;]): Kiểu xử lý khi gặp hai bản ghi cùng giá trị
                trong các unique cols. Nếu là `nothing` thì sẽ không làm gì cả, còn nếu là `update` thì sẽ update bản
                ghi cũ theo giá trị bản ghi mới. Defaults to &#39;nothing&#39;
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
        """
        Hỗ trợ lấy ngày lịch sử gần nhất mà pipeline đã lấy dữ liệu lịch sử của một khu vực.
        Thực chất để đảm bảo đồng bộ, vì thường ngày này thường là ngày làm việc gần nhất của
        thị trường chứng khoán.

        Args:
            region (Literal[&#39;americas&#39;, &#39;europe&#39;, &#39;asia_pacific&#39;]): Khu vực được hỗ trợ.
                Dữ liệu thường phải lấy theo khu vực vì timezone khác nhau.

        Returns:
            datetime: Trả về ngày gần nhất được lấy, nếu không nó sẽ lấy giá trị mặc định trong trường hợp bảng chưa tồn tại
                hoặc không tìm thấy dữ liệu tương ứng.
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
                    return datetime.combine(result, datetime.min.time()).replace(tzinfo=timezone.utc)
                return default_return_date # Trả về None nếu bảng trống
        except Exception as e:
            print(f"Lỗi khi truy vấn ngày cuối cùng từ CSDL: {e}")
            # Nếu có lỗi (ví dụ bảng chưa tồn tại), coi như chưa có dữ liệu
            return default_return_date
        
    def _load_ticker_metadata(self):
        """
        Tải thông tin chi tiết của tất cả các ticker đang hoạt động từ DB
        và lưu vào cache trong bộ nhớ.
        Hàm này chỉ nên được gọi một lần.
        """
        print("Loading ticker metadata into cache...")
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
        print(f"Metadata cache loaded with {len(self._ticker_info_cache)} active tickers.")
        
    def get_active_tickers_with_info(self) -> dict[str, dict[str, any]]:
        """
        Lấy danh sách các ticker đang hoạt động cùng với thông tin metadata của chúng.
        Sử dụng cơ chế cache để chỉ truy vấn DB một lần duy nhất.

        Returns:
            Dict[str, Dict[str, Any]]: Một dictionary với key là ticker và value là 
                                       một dict chứa thông tin chi tiết.
        """
        if self._ticker_info_cache is None:
            self._load_ticker_metadata()
        return self._ticker_info_cache
    
class RedisManager:
    def __init__(self):
        self._connection: Redis = None
        
    def get_connection(self) -> Redis:
        if self._connection is not None:
            return self._connection
        
        env_path = Path(__file__).parent.parent.parent / '.env'
        load_dotenv(env_path)
        
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        
        print(f"Get connection to redis {redis_host}:{redis_port}...")
        
        try:
            # decode_responses=True để kết quả trả về là string thay vì bytes
            self._connection = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=0,
                decode_responses=True
            )
            self._connection.ping()
            print("Successfully connect to redis!")
        except redis.exceptions.ConnectionError as e:
            print(f"Error when connect to Redis: {e}")
            raise
        
        return self._connection
    
    def save_candle(self, candle: dict, identify: str, ttl_seconds: int = 86400):
        try:
            if self._connection is None:
                self._connection = self.get_connection()
            conn = self._connection
            
            conn.hset(identify, mapping=candle)
            
            conn.expire(identify, ttl_seconds)
        except Exception as e:
            print(e)
            raise FetchException(f'An exception appear when save candle with name {identify}')
        
    def add_intraday_candle(self, ticker: str, candle_data: dict, max_entries: int = 300):
        """
        Thêm một cây nến 5 phút vào Redis Stream cho một ticker.
        Stream sẽ được tự động giới hạn kích thước.

        Args:
            ticker (str): Mã cổ phiếu.
            candle_data (dict): Dictionary chứa dữ liệu OHLCV.
            max_entries (int): Số lượng entry tối đa cần giữ lại trong stream.
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
            print(f"Lỗi khi thêm vào Redis Stream cho {ticker}: {e}")
            raise
            
db_mng = PostgreDBManager()
print(type(db_mng.get_active_tickers_with_info()['NVDA']['open_time']))