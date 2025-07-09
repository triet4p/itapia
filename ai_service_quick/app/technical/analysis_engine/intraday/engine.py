import pandas as pd
from typing import Dict, Any

from app.technical.analysis_engine.intraday.status_analyzer import IntradayStatusAnalyzer
from app.technical.analysis_engine.intraday.level_identifier import IntradayLevelIdentifier
from app.technical.analysis_engine.intraday.momentum_analyzer import IntradayMomentumAnalyzer

class IntradayAnalysisEngine:
    """
    Facade: Phân tích DataFrame intraday đã có đặc trưng và tạo báo cáo.
    Nó điều phối các chuyên gia phân tích intraday.
    """
    def __init__(self, feature_df: pd.DataFrame):
        if not isinstance(feature_df, pd.DataFrame) or feature_df.empty:
            raise ValueError("IntradayAnalysisEngine requires a non-empty pandas DataFrame.")
        if not isinstance(feature_df.index, pd.DatetimeIndex):
            raise TypeError("DataFrame index must be a DatetimeIndex for intraday analysis.")

        self.df = feature_df
        self.latest_row = self.df.iloc[-1]

        # Khởi tạo các chuyên gia intraday
        self.status_analyzer = IntradayStatusAnalyzer(self.df)
        self.level_identifier = IntradayLevelIdentifier(self.df)
        self.momentum_analyzer = IntradayMomentumAnalyzer(self.df)

    def get_analysis_report(self) -> Dict[str, Any]:
        """
        Tạo báo cáo phân tích intraday tổng hợp.
        """
        print("--- IntradayAnalysisEngine: Generating Intraday Report ---")
        
        report = {
            "current_status": self.status_analyzer.analyze_current_status(),
            "key_levels": self.level_identifier.identify_key_levels(),
            "momentum": self.momentum_analyzer.analyze_momentum_and_volume()
        }
        return report