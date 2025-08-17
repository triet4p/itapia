from datetime import datetime
from typing import Dict, Any
import pandas as pd

from itapia_common.dblib.services import BacktestReportService, APIMetadataService, APIPricesService
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Backtest Data Preparer')

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
    logger.info("Transforming single ticker repsonse ...")
    metadata = json_res.get('metadata')
    if not metadata:
        raise ValueError("Response is missing 'metadata' key.")
    
    data_points = json_res.get('datas')
    if not data_points:
        logger.warn(f"Empty data points for ticker {metadata.get('ticker')}. Returning empty DataFrame.")
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

class BacktestDataPreparer:
    def __init__(self, backtest_report_service: BacktestReportService,
                 metadata_service: APIMetadataService,
                 prices_service: APIPricesService):
        self.backtest_report_service = backtest_report_service
        self.metadata_service = metadata_service
        self.prices_service = prices_service
        
    def get_daily_ohlcv_for_ticker(self, ticker: str, limit: int = 2000) -> pd.DataFrame:
        """
        Lấy và chuyển đổi dữ liệu giá hàng ngày cho một ticker duy nhất.
        """
        logger.info(f"Preparing daily OHLCV for ticker '{ticker}'...")
        res = self.prices_service.get_daily_prices(ticker, limit=limit, skip=0)
        json_res = res.model_dump()
        if not json_res:
            logger.warn("Null response. Return empty DF.")
            return pd.DataFrame()
        
        try:
            df = transform_single_ticker_response(json_res)
            return df
        except ValueError as e:
            logger.err(f"Could not process a response. Error: {e}. Skipping.")
            return pd.DataFrame()
        
    def get_backtest_report(self, ticker: str, backtest_date: datetime):
        report = self.backtest_report_service.get_backtest_report(ticker, backtest_date)
        if report is None:
            raise ValueError("No report found for ticker: {}, backtest_date: {}".format(ticker, backtest_date))
        return report
    
    def get_backtest_reports_for_ticker(self, ticker: str):
        return self.backtest_report_service.get_all_backtest_reports(ticker)
    
    def get_all_tickers(self) -> list[str]:
        return [x.upper() for x in self.metadata_service.metadata_cache.keys()]
    
    