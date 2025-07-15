from app.data_prepare.data_access import *
from app.data_prepare.data_transform import *

from app.logger import *

class DataPrepareOrchestrator:
    """
    Điều phối toàn bộ quy trình chuẩn bị dữ liệu.
    Đây là giao diện duy nhất mà các module AI khác nên sử dụng để lấy dữ liệu.
    """

    def get_daily_ohlcv_for_ticker(self, ticker: str, limit: int = 2000) -> pd.DataFrame:
        """
        Lấy và chuyển đổi dữ liệu giá hàng ngày cho một ticker duy nhất.
        """
        info(f"DataPrepareOrchestrator: Preparing daily OHLCV for ticker '{ticker}'...")
        json_res = fetch_daily_prices_for_ticker(ticker, limit=limit)
        if not json_res:
            warn("DataPrepareOrchestrator: Null response. Return empty DF.")
            return pd.DataFrame()
        
        try:
            df = transform_single_ticker_response(json_res)
            return df
        except ValueError as e:
            err(f"Data Transformer: Could not process a response. Error: {e}. Skipping.")
            return pd.DataFrame()

    def get_daily_ohlcv_for_sector(self, sector_code: str, limit_per_ticker: int = 2000) -> pd.DataFrame:
        """
        Lấy và chuyển đổi dữ liệu giá hàng ngày cho tất cả các ticker trong một nhóm ngành,
        sau đó gộp chúng lại thành một DataFrame lớn.
        Rất hữu ích cho việc huấn luyện mô hình theo nhóm ngành.
        """
        info(f"DataPrepareOrchestrator: Preparing daily OHLCV for sector '{sector_code}'...")
        json_list = fetch_daily_prices_for_sector(sector_code, limit=limit_per_ticker)
        if not json_list:
            warn("DataPrepareOrchestrator: Null response. Return empty DF.")
            return pd.DataFrame()
        
        df = transform_multi_ticker_responses(json_list)
        return df

    def get_intraday_ohlcv_for_ticker(self, ticker: str) -> pd.DataFrame:
        """
        Lấy và chuyển đổi dữ liệu giá trong ngày cho một ticker duy nhất.
        """
        info(f"DataPrepareOrchestrator: Preparing intraday OHLCV for ticker '{ticker}'...")
        json_res = fetch_intraday_prices_for_ticker(ticker)
        if not json_res:
            warn("DataPrepareOrchestrator: Null response. Return empty DF.")
            return pd.DataFrame()
        
        try:
            df = transform_single_ticker_response(json_res)
            return df
        except ValueError as e:
            err(f"Data Transformer: Could not process a response. Error: {e}. Skipping.")
            return pd.DataFrame()
        
    def get_all_sectors_as_df(self) -> pd.DataFrame:
        """
        Lấy danh sách tất cả các nhóm ngành và trả về dưới dạng DataFrame.
        """
        info(f"DataPrepareOrchestrator: Preparing sector list...")
        sector_list = fetch_all_sectors()
        if not sector_list:
            warn("DataPrepareOrchestrator: Null response. Return empty DF.")
            return pd.DataFrame()
        info(f"DataPrepareOrchestrator: Transforming to DF...")
        return pd.DataFrame(sector_list)
    
    def get_all_sectors_code(self) -> List[str]:
        info(f"DataPrepareOrchestrator: Preparing sector list...")
        sector_list = fetch_all_sectors()
        if not sector_list:
            warn("DataPrepareOrchestrator: Null response. Return empty list.")
            return []
        
        return [x['sector_code'] for x in sector_list]