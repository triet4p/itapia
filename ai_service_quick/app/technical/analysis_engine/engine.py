import pandas as pd
from app.technical.analysis_engine.sr_identifier import SupportResistanceIdentifier
from app.technical.analysis_engine.trend_analyzer import TrendAnalyzer
from typing import Any, Dict

class AnalysisEngine:
    """
    Facade: Phân tích một DataFrame đã có đặc trưng và tạo ra một báo cáo.
    Nó điều phối các lớp chuyên gia để thực hiện các phân tích phức tạp.
    """
    def __init__(self, feature_df: pd.DataFrame, history_window: int = 90):
        """
        Khởi tạo với DataFrame đã được làm giàu bởi FeatureEngine.

        Args:
            feature_df (pd.DataFrame): DataFrame chứa các đặc trưng.
            history_window (int): Số ngày lịch sử để các analyzer xem xét.
        """
        if not isinstance(feature_df, pd.DataFrame) or feature_df.empty:
            raise ValueError("AnalysisEngine requires a non-empty pandas DataFrame.")
        
        self.df = feature_df
        # Lấy dòng dữ liệu cuối cùng để phân tích tình trạng hiện tại
        self.latest_row = self.df.iloc[-1]
        
        # --- KHỞI TẠO CÁC CHUYÊN GIA ---
        # Mỗi chuyên gia sẽ nhận DataFrame và tự xử lý phần dữ liệu nó cần.
        self.trend_analyzer = TrendAnalyzer(self.df)
        self.sr_identifier = SupportResistanceIdentifier(self.df, history_window=history_window)
        # self.pattern_recognizer = PatternRecognizer(self.df) # Sẽ thêm sau

    def get_analysis_report(self) -> Dict[str, Any]:
        """
        Tạo báo cáo tình trạng kỹ thuật tổng hợp bằng cách gọi các chuyên gia.
        """
        print("--- AnalysisEngine: Generating Full Analysis Report ---")
        
        # --- GỌI CÁC CHUYÊN GIA ĐỂ LẤY KẾT QUẢ PHÂN TÍCH ---
        trend_report = self.trend_analyzer.analyze_trend()
        sr_report = self.sr_identifier.identify_levels()
        
        # Tạm thời dùng giá trị placeholder cho module chưa có
        patterns_report = ["Pending Implementation"] 
        # Sau này sẽ thay thế bằng:
        # patterns_report = self.pattern_recognizer.find_patterns()

        # --- TỔNG HỢP THÀNH BÁO CÁO CUỐI CÙNG ---
        report = {
            "indicators": self._extract_key_indicators(),
            "trend": trend_report,
            "support_resistance": sr_report,
            "patterns": patterns_report,
        }
        return report

    def _extract_key_indicators(self) -> Dict[str, float]:
        """
        Trích xuất các giá trị chỉ báo quan trọng để hỗ trợ cả phân tích trung và dài hạn.
        """
        # Đảm bảo có tất cả các MA cần thiết: 20, 50, 200
        indicators_to_extract = [
            'SMA_20', 'SMA_50', 'SMA_200', 
            'RSI_14', 'ADX_14', 'DMP_14', 'DMN_14',
            'BBU_20_2.0', 'BBL_20_2.0', 'ATR_14'
        ]
        
        print("Extracting key indicators for multi-timeframe analysis...")
        key_indicators = {}
        for indicator in indicators_to_extract:
            if indicator in self.latest_row and pd.notna(self.latest_row[indicator]):
                key_indicators[indicator] = round(self.latest_row[indicator], 2)
            else:
                key_indicators[indicator] = None
                
        return key_indicators