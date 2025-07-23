from datetime import datetime, timezone
from typing import Literal
import numpy as np
import pandas as pd
from app.technical.orchestrator import TechnicalOrchestrator
from app.data_prepare.orchestrator import DataPrepareOrchestrator
from app.forecasting.orchestrator import ForecastingOrchestrator

from itapia_common.dblib.schemas.reports import QuickCheckReport, ErrorResponse
from itapia_common.dblib.services import APIMetadataService, APINewsService, APIPricesService
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Quick Check Orchestrator')

def clean_json_outliers(obj) -> dict:
    """
    Quét đệ quy qua một đối tượng (dict, list) và thay thế các giá trị
    numpy/float đặc biệt (inf, -inf, nan) bằng None.
    """
    if isinstance(obj, dict):
        return {k: clean_json_outliers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_outliers(elem) for elem in obj]
    elif isinstance(obj, (np.integer, np.floating, float)):
        # Kiểm tra xem có phải là nan, inf, hoặc -inf không
        if not np.isfinite(obj):
            return None  # Thay thế bằng None (sẽ trở thành null trong JSON)
    return obj


class AIServiceQuickOrchestrator:
    """
    Super Orchestrator ("CEO") cho toàn bộ quy trình Quick Check.
    Nó điều phối các orchestrator của từng module lớn để thực hiện các
    quy trình nghiệp vụ hoàn chỉnh.
    """
    def __init__(self, metadata_service: APIMetadataService,
                 prices_service: APIPricesService,
                 news_service: APINewsService):
        # Khởi tạo các "Trưởng phòng"
        self.data_preparer = DataPrepareOrchestrator(metadata_service, prices_service, news_service)
        self.tech_analyzer = TechnicalOrchestrator()
        self.forecaster = ForecastingOrchestrator(metadata_service)
        
    def get_full_analysis_report(self, ticker: str, 
                                 daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                                 required_type: Literal['daily', 'intraday', 'all']='all'):
        """
        QUY TRÌNH 1: Tạo báo cáo phân tích A-Z cho một ticker duy nhất.
        Bao gồm lấy dữ liệu, tạo features, và phân tích.
        """
        logger.info(f"--- CEO: Initiating full analysis for ticker '{ticker}' ---")
        
        # --- BƯỚC 1: LẤY DỮ LIỆU THÔ ---
        # Ra lệnh cho "Trưởng phòng Chuẩn bị Dữ liệu"
        logger.info("CEO -> DataPreparer: Fetching daily and intraday data...")
        daily_df = self.data_preparer.get_daily_ohlcv_for_ticker(ticker)
        intraday_df = self.data_preparer.get_intraday_ohlcv_for_ticker(ticker)

        if daily_df.empty and intraday_df.empty:
            logger.err(f"No data available for ticker {ticker}.")
            return ErrorResponse(error=f"No data available for ticker {ticker}.")

        # --- BƯỚC 2: THỰC HIỆN PHÂN TÍCH KỸ THUẬT ---
        # Ra lệnh cho "Trưởng phòng Kỹ thuật"
        logger.info("CEO -> TechAnalyzer: Performing analyses...")
        technical_analysis_report = self.tech_analyzer.get_full_analysis(daily_df, 
                                                                         intraday_df,
                                                                         required_type=required_type,
                                                                         daily_analysis_type=daily_analysis_type)
        
        # --- BƯỚC 3 (TƯƠNG LAI): GỌI CÁC PHÒNG BAN KHÁC ---
        # forecast_report = self.forecaster.get_forecast(...)
        # news_report = self.news_analyzer.get_sentiment(...)
        X = self.tech_analyzer.get_daily_features(daily_df)
        X_instance = X.iloc[-1:]
        forecast_report = self.forecaster.generate_report(X_instance, ticker)
        news_report = {"status": "News module pending."}

        generate_time = datetime.now(tz=timezone.utc)

        # --- BƯỚC 4: TỔNG HỢP KẾT QUẢ ---
        final_report = QuickCheckReport(
            ticker=ticker.upper(),
            generated_at_utc=generate_time.isoformat(),
            generated_timestamp=int(generate_time.timestamp()),
            technical_report=technical_analysis_report,
            forecasting_report=forecast_report,
            news_report=news_report
        )
        
        logger.info(f"--- CEO: Full analysis for '{ticker}' complete. ---")
        
        cleaned_report_dict = clean_json_outliers(final_report.model_dump())
        
        return QuickCheckReport.model_validate(cleaned_report_dict)
    
    async def preload_all_caches(self):
        """
        Kích hoạt quy trình làm nóng cache cho tất cả các module cần thiết.
        """
        logger.info("--- CEO: Starting pre-warming process for all sub-modules ---")
        # Gọi đến hàm preload của "trưởng phòng" forecasting
        await self.forecaster.preload_caches_for_all_sectors()
        logger.info("--- CEO: Pre-warming complete ---")
    
    def prepare_training_data_for_sector(self, sector_code: str) -> pd.DataFrame:
        """
        QUY TRÌNH 2: Chuẩn bị một DataFrame lớn, sẵn sàng để huấn luyện,
        cho tất cả các ticker trong một nhóm ngành.
        """
        logger.info(f"--- CEO: Preparing training data for sector '{sector_code}' ---")
        
        # BƯỚC 1: LẤY DỮ LIỆU GỘP CỦA CẢ NGÀNH
        logger.info("CEO -> DataPreparer: Fetching and transforming sector data...")
        sector_ohlcv_df = self.data_preparer.get_daily_ohlcv_for_sector(sector_code)
        
        if sector_ohlcv_df.empty:
            logger.err(f"No data found for sector {sector_code}.")
            return pd.DataFrame()

        # BƯỚC 2: TẠO FEATURES CHO DỮ LIỆU ĐÃ GỘP
        # Lưu ý: Cần lặp qua từng ticker để tạo feature cho đúng
        logger.info("CEO -> TechAnalyzer: Generating features for sector data...")
        all_enriched_dfs = []
        for ticker, group_df in sector_ohlcv_df.groupby('ticker'):
            logger.info(f"  - Generating features for {ticker}...")
            enriched_ticker_df = self.tech_analyzer.get_daily_features(group_df)
            all_enriched_dfs.append(enriched_ticker_df)
        
        enriched_sector_df = pd.concat(all_enriched_dfs)

        # BƯỚC 3 (TƯƠNG LAI): TẠO TARGETS
        # training_ready_df = self.forecasting_pipeline.create_targets(enriched_sector_df)
        
        logger.info(f"--- CEO: Training data for '{sector_code}' is ready. ---")
        return enriched_sector_df # Tạm thời trả về df đã có features
    
    def export_local_data_for_sector(self, sector_code: str):
        df = self.prepare_training_data_for_sector(sector_code)
        df.to_csv(f'/ai-service-quick/local/training_{sector_code}.csv')
        
if __name__ == '__main__':
    import sys
    sector = sys.argv[1]
    orchestrator = AIServiceQuickOrchestrator()
    orchestrator.export_local_data_for_sector(sector)