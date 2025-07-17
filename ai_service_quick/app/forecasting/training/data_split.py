from typing import Generator, Tuple
import pandas as pd
from datetime import datetime

def train_test_split(df: pd.DataFrame,
                     train_test_split_date: datetime,
                     test_last_date: datetime):
 
    df_train = df[df.index <= train_test_split_date]
    df_test = df[(df.index > train_test_split_date) & (df.index <= test_last_date)]
    
    return df_train, df_test

def get_walk_forward_splits(
    df: pd.DataFrame, 
    validation_months: int = 3,
    min_train_months: int = 6
) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
    """
    Tạo các cặp (train, validation) cho quy trình Walk-Forward Validation theo từng năm,
    với kích thước tập validation có thể tùy chỉnh.

    Hàm này chia dữ liệu thành các khối hàng năm. Trong mỗi năm, một số tháng cuối cùng
    (được xác định bởi `validation_months`) được dùng làm tập validation, và phần còn lại
    của năm đó cộng với tất cả các năm trước đó được dùng làm tập train.

    Args:
        df (pd.DataFrame): DataFrame đầu vào, phải có DatetimeIndex.
        validation_months (int, optional): Số tháng cuối của mỗi năm được dùng làm
            tập validation. Mặc định là 3 (tức là Q4).
        min_train_months (int, optional): Số tháng tối thiểu trong một năm để được coi
            là một "khối" hợp lệ cho việc chia. Giúp bỏ qua các năm có quá ít dữ liệu.

    Yields:
        Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]: 
            Một generator, mỗi lần yield ra một cặp (train_df, valid_df).
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("DataFrame index must be a DatetimeIndex.")
    if not 1 <= validation_months <= 11:
        raise ValueError("validation_months must be between 1 and 11.")

    # Sắp xếp để đảm bảo thứ tự thời gian
    df = df.sort_index()
    
    start_year = df.index.min().year
    end_year = df.index.max().year

    print(f"Generating splits from {start_year} to {end_year} with {validation_months}-month validation...")

    for year in range(start_year, end_year + 1):
        year_data = df[df.index.year == year]

        # Kiểm tra xem năm hiện tại có đủ dữ liệu không
        if year_data.index.month.nunique() < min_train_months:
            print(f"  - Skipping year {year}: not enough data.")
            continue

        # Xác định tháng bắt đầu của tập validation
        # Ví dụ: nếu validation_months=3, val_start_month sẽ là 10 (tháng 10)
        val_start_month = 12 - validation_months + 1
        
        valid_df = year_data[year_data.index.month >= val_start_month]

        # Xử lý trường hợp năm cuối cùng có thể không có đủ tháng validation
        if valid_df.empty:
            print(f"  - Skipping validation for year {year}: no data in the last {validation_months} months.")
            continue
            
        validation_start_date = valid_df.index.min()
        train_df = df[df.index < validation_start_date]

        if not train_df.empty:
            print(f"  - Yielding Split for year {year}:")
            print(f"    - Train: {train_df.index.min().date()} -> {train_df.index.max().date()} (shape: {train_df.shape})")
            print(f"    - Valid: {valid_df.index.min().date()} -> {valid_df.index.max().date()} (shape: {valid_df.shape})")
            yield train_df, valid_df