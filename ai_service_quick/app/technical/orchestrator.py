from typing import Any, Dict, Literal
from app.technical.feature_engine import DailyFeatureEngine, IntradayFeatureEngine
from app.technical.analysis_engine.daily import DailyAnalysisEngine
from app.technical.analysis_engine.intraday import IntradayAnalysisEngine

import pandas as pd

class TechnicalOrchestrator:
    def get_daily_features(self, ohlcv_df: pd.DataFrame):
        print("--- TechOrchestrator Service: get_daily_features ---")
        engine = DailyFeatureEngine(ohlcv_df)
        return engine.add_all_features().get_features(handle_na_method='forward_fill', 
                                                      reset_index=False)
        
    def get_intraday_features(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """SERVICE 2: Chỉ tạo và trả về DataFrame đặc trưng trong ngày."""
        print("--- TechOrchestrator Service: get_intraday_features ---")
        engine = IntradayFeatureEngine(ohlcv_df)
        return engine.add_all_intraday_features().get_features(handle_na_method='forward_fill',
                                                               reset_index=False)
        
    def get_daily_analysis(self, enriched_df: pd.DataFrame) -> Dict[str, Any]:
        """SERVICE 3: Chỉ phân tích một DataFrame hàng ngày đã có đặc trưng."""
        print("--- TechOrchestrator Service: get_daily_analysis ---")
        if enriched_df.empty:
            return {"error": "Cannot analyze empty enriched DataFrame."}
        engine = DailyAnalysisEngine(enriched_df)
        return engine.get_analysis_report()
        
    def get_intraday_analysis(self, enriched_df: pd.DataFrame) -> Dict[str, Any]:
        """SERVICE 4: Chỉ phân tích một DataFrame trong ngày đã có đặc trưng."""
        print("--- TechOrchestrator Service: get_intraday_analysis ---")
        if enriched_df.empty:
            return {"error": "Cannot analyze empty enriched DataFrame."}
        engine = IntradayAnalysisEngine(enriched_df)
        return engine.get_analysis_report()
    
    def _get_full_daily_analysis(self, ohlcv_df: pd.DataFrame):
        enriched_df = self.get_daily_features(ohlcv_df)
        return self.get_daily_analysis(enriched_df)
    
    def _get_full_intraday_analysis(self, ohlcv_df: pd.DataFrame):
        enriched_df = self.get_intraday_features(ohlcv_df)
        return self.get_intraday_analysis(enriched_df)
    
    def get_full_analysis(self, ohlcv_df: pd.DataFrame,
                          required_type: Literal['daily', 'intraday', 'all'] = 'all'):
        full_report = {
            'type': required_type
        }
        
        if required_type == 'daily' or required_type == 'all':
            full_report['daily'] = self._get_full_daily_analysis(ohlcv_df)
        if required_type == 'intraday' or required_type == 'all':
            full_report['intraday'] = self._get_full_intraday_analysis(ohlcv_df)
            
        return full_report
             