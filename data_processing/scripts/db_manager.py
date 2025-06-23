from datetime import datetime, timedelta
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.schema import Table, MetaData
from sqlalchemy.dialects.postgresql import insert as pg_insert
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
from typing import Literal

from utils import TO_FETCH_TICKERS_BY_REGION, FetchException, DEFAULT_START_DATE

def get_postgre_engine() -> Engine:
    """
    Lấy một Engine để truy cập và kết nối tới CSDL Postgre.
    Các thông tin về user, password, db name cần được nạp vào file `.env` ở thư mục gốc.

    Raises:
        FetchException: Khi không tìm được file cấu hình hoặc kết nối bị sai

    Returns:
        Engine: Engine giúp kết nối CSDL
    """
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
    
def bulk_upsert_json(engine: Engine, table_name: str,
                     data: list[dict],
                     unique_cols: list[str],
                     chunk_size: int = 1000):
    """
    Hỗ trợ thao tác insert on duplicate update trên 1 loạt bản ghi.
    Các bản ghi sẽ được upsert theo transaction. Nếu 1 bản ghi bị lỗi
    thì cả quá trình sẽ không được ghi nhận

    Args:
        engine (Engine): Một Engine hỗ trợ kết nối CSDL
        table_name (str): Tên bảng cần upsert
        data (list[dict]): Dữ liệu, là một list các dict, mỗi dict phải gồm các key là tên các cột
        unique_cols (list[str]): Các cột được lấy là điều kiện UNIQUE. Nếu 2 hàng có các dữ liệu trên
            các cột unique này trùng nhau thì sẽ được update.
        chunk_size (int): Số hàng trong 1 batch được chèn vào. Defaults to 1000.
    """
    if not data:
        print('DF is empty!!')
        return 
    
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
            print(f"Đã xử lý {total_inserted}/{len(data)} dòng...")

    print(f"Hoàn tất. Upsert thành công {total_inserted} dòng vào bảng '{table_name}'.")
    
def bulk_upsert_df(engine: Engine, table_name: str,
                   df: pd.DataFrame,
                   unique_cols: list[str],
                   chunk_size: int = 1000):
    """
    Hỗ trợ thao tác insert on duplicate update trên 1 loạt bản ghi.
    Các bản ghi sẽ được upsert theo transaction. Nếu 1 bản ghi bị lỗi
    thì cả quá trình sẽ không được ghi nhận.
    
    Phương thức này hỗ trợ làm việc trên `DataFrame` của `pandas`.

    Args:
        engine (Engine): Một Engine hỗ trợ kết nối CSDL
        table_name (str): Tên bảng cần upsert
        df (pd.DataFrame): DataFrame chứa dữ liệu cần upsert, cần có đủ các column cần thiết.
        unique_cols (list[str]): Các cột được lấy là điều kiện UNIQUE. Nếu 2 hàng có các dữ liệu trên
            các cột unique này trùng nhau thì sẽ được update.
        chunk_size (int): Số hàng trong 1 batch được chèn vào. Defaults to 1000.
    """
    if df.empty:
        print('DF is empty!!')
        return 
    
    data = df.to_dict(orient='records')
    bulk_upsert_json(engine, table_name, data, unique_cols, chunk_size)
    
def get_last_history_date(engine: Engine, region: Literal['americas', 'europe', 'asia_pacific']):
    """
    Hỗ trợ lấy ngày lịch sử gần nhất mà pipeline đã lấy dữ liệu lịch sử của một khu vực.
    Thực chất để đảm bảo đồng bộ, vì thường ngày này thường là ngày làm việc gần nhất của
    thị trường chứng khoán.

    Args:
        engine (Engine): Một Engine hỗ trợ kết nối CSDL
        region (Literal[&#39;americas&#39;, &#39;europe&#39;, &#39;asia_pacific&#39;]): Khu vực được hỗ trợ.
            Dữ liệu thường phải lấy theo khu vực vì timezone khác nhau.

    Returns:
        datetime: Trả về ngày gần nhất được lấy, nếu không nó sẽ lấy giá trị mặc định trong trường hợp bảng chưa tồn tại
            hoặc không tìm thấy dữ liệu tương ứng.
    """
    default_return_date = DEFAULT_START_DATE - timedelta(days=1)
    
    if region not in ['americas', 'europe', 'asia_pacific']:
        print('Not support region, return default')
        return default_return_date
    
    tickers = tuple(TO_FETCH_TICKERS_BY_REGION[region])
    query = f"SELECT MAX(collect_date) FROM history_prices WHERE ticker IN {tickers};"
    stmt = text(query)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(stmt).scalar()
            if result:
                # Chuyển đổi từ date của DB sang datetime của Python
                return datetime.combine(result, datetime.min.time())
            return default_return_date # Trả về None nếu bảng trống
    except Exception as e:
        print(f"Lỗi khi truy vấn ngày cuối cùng từ CSDL: {e}")
        # Nếu có lỗi (ví dụ bảng chưa tồn tại), coi như chưa có dữ liệu
        return default_return_date
    

    
