from datetime import datetime, timezone
from typing import Literal
import pandas as pd
from app.technical.orchestrator import TechnicalOrchestrator
from app.data_prepare.orchestrator import DataPrepareOrchestrator

from app.logger import *

class AIServiceQuickOrchestrator:
    """
    Super Orchestrator ("CEO") cho toàn bộ quy trình Quick Check.
    Nó điều phối các orchestrator của từng module lớn để thực hiện các
    quy trình nghiệp vụ hoàn chỉnh.
    """
    def __init__(self):
        # Khởi tạo các "Trưởng phòng"
        self.data_preparer = DataPrepareOrchestrator()
        self.tech_analyzer = TechnicalOrchestrator()
        
    def get_full_analysis_report(self, ticker: str, 
                                 daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium'):
        """
        QUY TRÌNH 1: Tạo báo cáo phân tích A-Z cho một ticker duy nhất.
        Bao gồm lấy dữ liệu, tạo features, và phân tích.
        """
        info(f"--- CEO: Initiating full analysis for ticker '{ticker}' ---")
        
        # --- BƯỚC 1: LẤY DỮ LIỆU THÔ ---
        # Ra lệnh cho "Trưởng phòng Chuẩn bị Dữ liệu"
        info("CEO -> DataPreparer: Fetching daily and intraday data...")
        daily_df = self.data_preparer.get_daily_ohlcv_for_ticker(ticker)
        intraday_df = self.data_preparer.get_intraday_ohlcv_for_ticker(ticker)

        if daily_df.empty and intraday_df.empty:
            err(f"No data available for ticker {ticker}.")
            return {"error": f"No data available for ticker {ticker}."}

        # --- BƯỚC 2: THỰC HIỆN PHÂN TÍCH KỸ THUẬT ---
        # Ra lệnh cho "Trưởng phòng Kỹ thuật"
        info("CEO -> TechAnalyzer: Performing analyses...")
        technical_analysis_report = self.tech_analyzer.get_full_analysis(daily_df, 
                                                                         intraday_df,
                                                                         required_type='daily',
                                                                         daily_analysis_type=daily_analysis_type)
        
        # --- BƯỚC 3 (TƯƠNG LAI): GỌI CÁC PHÒNG BAN KHÁC ---
        # forecast_report = self.forecaster.get_forecast(...)
        # news_report = self.news_analyzer.get_sentiment(...)
        forecast_report = {"status": "Forecasting module pending."}
        news_report = {"status": "News module pending."}

        generate_time = datetime.now(tz=timezone.utc)

        # --- BƯỚC 4: TỔNG HỢP KẾT QUẢ ---
        final_report = {
            "ticker": ticker.upper(),
            "generated_at_utc": generate_time.isoformat(),
            "generated_timestamp": int(generate_time.timestamp()),
            "analysis_type": "Quick Check Full Report",
            "technical_analysis": technical_analysis_report,
            "forecasting": forecast_report,
            "news": news_report
        }
        
        info(f"--- CEO: Full analysis for '{ticker}' complete. ---")
        return final_report
    
    def prepare_training_data_for_sector(self, sector_code: str) -> pd.DataFrame:
        """
        QUY TRÌNH 2: Chuẩn bị một DataFrame lớn, sẵn sàng để huấn luyện,
        cho tất cả các ticker trong một nhóm ngành.
        """
        info(f"--- CEO: Preparing training data for sector '{sector_code}' ---")
        
        # BƯỚC 1: LẤY DỮ LIỆU GỘP CỦA CẢ NGÀNH
        info("CEO -> DataPreparer: Fetching and transforming sector data...")
        sector_ohlcv_df = self.data_preparer.get_daily_ohlcv_for_sector(sector_code)
        
        if sector_ohlcv_df.empty:
            err(f"No data found for sector {sector_code}.")
            return pd.DataFrame()

        # BƯỚC 2: TẠO FEATURES CHO DỮ LIỆU ĐÃ GỘP
        # Lưu ý: Cần lặp qua từng ticker để tạo feature cho đúng
        info("CEO -> TechAnalyzer: Generating features for sector data...")
        all_enriched_dfs = []
        for ticker, group_df in sector_ohlcv_df.groupby('ticker'):
            info(f"  - Generating features for {ticker}...")
            enriched_ticker_df = self.tech_analyzer.get_daily_features(group_df)
            all_enriched_dfs.append(enriched_ticker_df)
        
        enriched_sector_df = pd.concat(all_enriched_dfs)

        # BƯỚC 3 (TƯƠNG LAI): TẠO TARGETS
        # training_ready_df = self.forecasting_pipeline.create_targets(enriched_sector_df)
        
        info(f"--- CEO: Training data for '{sector_code}' is ready. ---")
        return enriched_sector_df # Tạm thời trả về df đã có features
    
    def export_local_data_for_sector(self, sector_code: str):
        df = self.prepare_training_data_for_sector(sector_code)
        df.to_csv(f'/ai-service-quick/local/training_{sector_code}.csv')
        
if __name__ == '__main__':
    orchestrator = AIServiceQuickOrchestrator()
    orchestrator.export_local_data_for_sector('TECH')