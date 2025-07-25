from app.data_prepare.data_transform import *

import app.core.config as cfg

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
        """
        Lấy danh sách các nhóm ngành và trả về dưới dạng List các code (string).
        """
        logger.info(f"Preparing sector list...")
        sector_list = self.metadata_service.get_all_sectors()
        sector_list = [x.sector_code for x in sector_list]
        if not sector_list:
            logger.warn("Null response. Return empty list.")
            return []
        
        return sector_list
    
    def get_sector_code_of(self, ticker: str):
        return self.metadata_service.get_sector_code_of(ticker)
    
    def is_exist(self, ticker: str):
        try:
            self.metadata_service.get_validate_ticker_info(ticker, 'news')
            return True
        except ValueError as e:
            return False
    
    def get_all_news_text_for_ticker(self, ticker: str) -> List[str]:
        def _get_full_text_from_news(news):
            text: str = news.title 
            if news.summary is not None:
                text += '.' + news.summary
            return text
        
        logger.info(f"Preparing combined news feed for ticker: {ticker}")
        sector_list = self.metadata_service.get_all_sectors()
        sector_code = self.get_sector_code_of(ticker)
        for x in sector_list:
            if x.sector_code == sector_code:
                sector = x.sector_name
                break
        
        all_news_text_with_time = []
        
        logger.info(f"Fetching L1 (Relevant) news...")
        relevant_news = self.news_service.get_relevant_news(ticker, skip=0, limit=cfg.NEWS_COUNT_RELEVANT)
        for news in relevant_news.datas:
            all_news_text_with_time.append((_get_full_text_from_news(news), news.publish_ts))
            
        universal_news_hash = set()
            
        logger.info(f"Fetching L2 (Contextual) universal news...")
        contextual_search_terms = f'{sector}' 
        contextual_news = self.news_service.get_universal_news(contextual_search_terms, 
                                                               skip=0, limit=cfg.NEWS_COUNT_CONTEXTUAL)
        for news in contextual_news.datas:
            if news.title_hash not in universal_news_hash:
                universal_news_hash.add(news.title_hash)
                all_news_text_with_time.append((_get_full_text_from_news(news), news.publish_ts))
                
        logger.info(f"Fetching L3 (Macro) universal news...")
        macro_search_terms_lst = ["Federal Reserve policy", "US inflation report CPI", "S&P 500"]
        for macro_search_terms in macro_search_terms_lst:
            macro_news = self.news_service.get_universal_news(macro_search_terms, 
                                                            skip=0, limit=cfg.NEWS_COUNT_MACRO)
            for news in macro_news.datas:
                if news.title_hash not in universal_news_hash:
                    universal_news_hash.add(news.title_hash)
                    all_news_text_with_time.append((_get_full_text_from_news(news), news.publish_ts))
        
        all_news_text_with_time.sort(key=lambda x: x[1], reverse=True)
        
        return [x[0] for x in all_news_text_with_time[:cfg.NEWS_TOTAL_LIMIT]]