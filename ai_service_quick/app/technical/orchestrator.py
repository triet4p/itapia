import pandas as pd

from typing import Any, Dict, Literal

from app.technical.feature_engine import DailyFeatureEngine, IntradayFeatureEngine
from app.technical.analysis_engine.daily import DailyAnalysisEngine
from app.technical.analysis_engine.intraday import IntradayAnalysisEngine

from itapia_common.dblib.schemas.reports.technical_analysis import TechnicalReport
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Technical Orchestrator')

class TechnicalOrchestrator:
    def get_daily_features(self, ohlcv_df: pd.DataFrame):
        logger.info("GENERATE DAILY FEATURES")
        try:
            engine = DailyFeatureEngine(ohlcv_df)
            return engine.add_all_features().get_features(handle_na_method='forward_fill', 
                                                        reset_index=False)
        except (ValueError, TypeError) as e:
            logger.err(f"Daily Feature Engine: {e}. Returning empty DataFrame.")
            return pd.DataFrame()
            

    def get_intraday_features(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        logger.info("GENERATE INTRADAY FEATURES")
        try:
            engine = IntradayFeatureEngine(ohlcv_df)
            return engine.add_all_intraday_features().get_features(handle_na_method='forward_fill',
                                                                reset_index=False)
        except (ValueError, TypeError) as e:
            logger.err(f"Intraday Feature Engine: {e}. Returning empty DataFrame.")
            return pd.DataFrame()
        
    def get_daily_analysis(self, enriched_df: pd.DataFrame,
                           analysis_type: Literal['short', 'medium', 'long'] = 'medium'):
        logger.info("GENERATE DAILY ANALYSIS")
        try:
            # DailyAnalysisEngine có thể ném ra ValueError nếu không đủ dữ liệu
            engine = DailyAnalysisEngine(enriched_df, analysis_type=analysis_type)
            return engine.get_analysis_report()
        except (ValueError, TypeError) as e:
            logger(f"Daily Analysis Engine: {e}. Returning error report.")
        
    def get_intraday_analysis(self, enriched_df: pd.DataFrame):
        logger.info("GENERATE DAILY ANALYSIS")
        try:
            # DailyAnalysisEngine có thể ném ra ValueError nếu không đủ dữ liệu
            engine = IntradayAnalysisEngine(enriched_df)
            return engine.get_analysis_report()
        except (ValueError, TypeError) as e:
            logger.err(f"Daily Analysis Engine: {e}. Returning error report.")
    
    def _get_full_daily_analysis(self, ohlcv_df: pd.DataFrame,
                                 analysis_type: Literal['short', 'medium', 'long'] = 'medium'):
        enriched_df = self.get_daily_features(ohlcv_df)
        return self.get_daily_analysis(enriched_df, analysis_type)
    
    def _get_full_intraday_analysis(self, ohlcv_df: pd.DataFrame):
        enriched_df = self.get_intraday_features(ohlcv_df)
        return self.get_intraday_analysis(enriched_df)
    
    def get_full_analysis(self, ohlcv_daily_df: pd.DataFrame,
                          ohlcv_intraday_df: pd.DataFrame,
                          required_type: Literal['daily', 'intraday', 'all'] = 'all',
                          daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium'):
        daily_report = None
        intraday_report = None
        
        if required_type == 'daily' or required_type == 'all':
            daily_report = self._get_full_daily_analysis(ohlcv_daily_df, daily_analysis_type)
        if required_type == 'intraday' or required_type == 'all':
            intraday_report = self._get_full_intraday_analysis(ohlcv_intraday_df)
            
        return TechnicalReport(
            report_type=required_type,
            daily_report=daily_report,
            intraday_report=intraday_report
        )
             