import pandas as pd
from typing import List, Dict, Any

from app.logger import *

def transform_single_ticker_response(json_res: Dict[str, Any]) -> pd.DataFrame:
    """
    Chuyển đổi response JSON cho một ticker duy nhất thành một DataFrame.
    DataFrame sẽ có DatetimeIndex.

    Args:
        json_res (Dict[str, Any]): Response JSON có chứa 'metadata' và 'datas'.

    Returns:
        pd.DataFrame: DataFrame OHLCV với DatetimeIndex.
    
    Raises:
        ValueError: Nếu response thiếu các key cần thiết.
    """
    # --- BƯỚC 1: VALIDATE VÀ TRÍCH XUẤT DỮ LIỆU ---
    info("Data Transformer: Transforming single ticker repsonse ...")
    metadata = json_res.get('metadata')
    if not metadata:
        raise ValueError("Response is missing 'metadata' key.")
    
    data_points = json_res.get('datas')
    if not data_points:
        warn(f"Data Transformer: Empty data points for ticker {metadata.get('ticker')}. Returning empty DataFrame.")
        return pd.DataFrame()

    # --- BƯỚC 2: CHUYỂN ĐỔI LIST DICT THÀNH DATAFRAME ---
    df = pd.DataFrame(data_points)

    # Kiểm tra các cột cần thiết trong data_points
    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Data points are missing required keys. Expected: {required_cols}")

    # --- BƯỚC 3: XỬ LÝ INDEX THỜI GIAN ---
    # Chuyển đổi cột timestamp (Unix epoch) thành DatetimeIndex UTC
    df['datetime_utc'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
    df.set_index('datetime_utc', inplace=True)
    df.drop(columns=['timestamp'], inplace=True) # Bỏ cột timestamp số
    
    # Sắp xếp theo thời gian để đảm bảo tính tuần tự
    df.sort_index(inplace=True)

    return df

def transform_multi_ticker_responses(json_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Chuyển đổi một danh sách các response JSON (mỗi response cho một ticker)
    thành một DataFrame duy nhất, được nối lại với nhau.
    Hàm này rất hữu ích cho việc chuẩn bị dữ liệu huấn luyện.

    Args:
        json_list (List[Dict[str, Any]]): Danh sách các đối tượng JSON response.

    Returns:
        pd.DataFrame: Một DataFrame lớn chứa dữ liệu của tất cả các ticker.
    """
    all_dfs = []
    
    info(f"Data Transformer Transforming data for {len(json_list)} tickers...")
    
    for json_res in json_list:
        try:
            # --- TÁI SỬ DỤNG LOGIC CỦA HÀM TRÊN ---
            # Lấy metadata
            metadata = json_res.get('metadata')
            if not metadata or not metadata.get('ticker'):
                warn("Data Transformer: Found a response with missing metadata or ticker. Skipping.")
                continue
            
            # Chuyển đổi dữ liệu chuỗi thời gian
            single_df = transform_single_ticker_response(json_res)
            
            if not single_df.empty:
                # Thêm một cột 'ticker' để phân biệt dữ liệu
                single_df['ticker'] = metadata['ticker']
                all_dfs.append(single_df)

        except ValueError as e:
            err(f"Data Transformer: Could not process a response. Error: {e}. Skipping.")
            continue

    if not all_dfs:
        warn("Data Transformer: No valid data found to concatenate.")
        return pd.DataFrame()

    # Nối tất cả các DataFrame nhỏ lại thành một DataFrame lớn
    final_df = pd.concat(all_dfs)
    
    return final_df