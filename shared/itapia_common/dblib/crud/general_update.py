# common/dblib/crud/general_update.py

from typing import Literal

import pandas as pd

from sqlalchemy import Engine
from sqlalchemy.schema import Table, MetaData
from sqlalchemy.dialects.postgresql import insert as pg_insert

def _bulk_insert_on_conflict_do_nothing(engine: Engine, table_name: str,
                                        data: list[dict],
                                        unique_cols: list[str],
                                        chunk_size: int = 1000):
    
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

def _bulk_insert_on_conflict_do_update(engine: Engine, table_name: str,
                                       data: list[dict],
                                       unique_cols: list[str],
                                       chunk_size: int = 1000):
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
    
def bulk_insert(engine: Engine, table_name: str, 
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
        _bulk_insert_on_conflict_do_nothing(engine, table_name, _data, unique_cols, chunk_size)
    else:
        _bulk_insert_on_conflict_do_update(engine, table_name, _data, unique_cols, chunk_size)
        
