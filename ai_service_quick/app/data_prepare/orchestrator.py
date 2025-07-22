from app.data_prepare.data_transform import *

from itapia_common.dblib.services import APIMetadataService, APINewsService, APIPricesService
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Data Prepare Orchestrator') 

class DataPrepareOrchestrator:
    """
    Điều phối toàn bộ quy trình chuẩn bị dữ liệu.
    Đây là giao diện duy nhất mà các module AI khác nên sử dụng để lấy dữ liệu.
    """
    
    def __init__(self, metadata_service: APIMetadataService,
                 prices_service: APIPricesService,
                 news_service: APINewsService):
        self.metadata_service = metadata_service
        self.prices_service = prices_service
        self.news_service = news_service

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

    def get_daily_ohlcv_for_sector(self, sector_code: str, limit_per_ticker: int = 2000) -> pd.DataFrame:
        """
        Lấy và chuyển đổi dữ liệu giá hàng ngày cho tất cả các ticker trong một nhóm ngành,
        sau đó gộp chúng lại thành một DataFrame lớn.
        Rất hữu ích cho việc huấn luyện mô hình theo nhóm ngành.
        """
        logger.info(f"Preparing daily OHLCV for sector '{sector_code}'...")
        res_lst = self.prices_service.get_daily_prices_by_sector(sector_code, limit=limit_per_ticker, skip=0)
        json_list = [x.model_dump() for x in res_lst]
        if not json_list:
            logger.warn("Null response. Return empty DF.")
            return pd.DataFrame()
        
        df = transform_multi_ticker_responses(json_list)
        return df

    def get_intraday_ohlcv_for_ticker(self, ticker: str) -> pd.DataFrame:
        """
        Lấy và chuyển đổi dữ liệu giá trong ngày cho một ticker duy nhất.
        """
        logger.info(f"Preparing intraday OHLCV for ticker '{ticker}'...")
        json_res = self.prices_service.get_intraday_prices(ticker).model_dump()
        if not json_res:
            logger.warn("Null response. Return empty DF.")
            return pd.DataFrame()
        
        try:
            df = transform_single_ticker_response(json_res)
            return df
        except ValueError as e:
            logger.err(f"Could not process a response. Error: {e}. Skipping.")
            return pd.DataFrame()
        
    def get_all_sectors_as_df(self) -> pd.DataFrame:
        """
        Lấy danh sách tất cả các nhóm ngành và trả về dưới dạng DataFrame.
        """
        logger.info(f"Preparing sector list...")
        sector_list = self.metadata_service.get_all_sectors()
        sector_list = [x.model_dump() for x in sector_list]
        if not sector_list:
            logger.warn("Null response. Return empty DF.")
            return pd.DataFrame()
        logger.info(f"Transforming to DF...")
        return pd.DataFrame(sector_list)
    
    def get_all_sectors_code(self) -> List[str]:
        logger.info(f"Preparing sector list...")
        sector_list = self.metadata_service.get_all_sectors()
        sector_list = [x.sector_code for x in sector_list]
        if not sector_list:
            logger.warn("Null response. Return empty list.")
            return []
        
        return [x['sector_code'] for x in sector_list]