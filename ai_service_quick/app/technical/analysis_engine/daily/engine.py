import pandas as pd

from typing import Any, Dict, Literal, Optional

from app.technical.analysis_engine.daily.sr_identifier import DailySRIdentifier
from app.technical.analysis_engine.daily.trend_analyzer import DailyTrendAnalyzer
from app.technical.analysis_engine.daily.pattern_recognizer import DailyPatternRecognizer

from app.logger import *

class DailyAnalysisEngine:
    """Facade điều phối các chuyên gia phân tích dữ liệu hàng ngày.

    Lớp này nhận một DataFrame đã có đặc trưng và điều phối các analyzer con
    (Trend, Support/Resistance, Pattern) để tạo ra một báo cáo phân tích
    kỹ thuật tổng hợp. Nó cho phép tùy chỉnh "phong cách phân tích"
    (short, medium, long) bằng cách truyền các bộ tham số khác nhau xuống
    các lớp con.
    """
    PARAMS_BY_PERIOD = {
        "short": {
            "history_window": 30,
            "prominence_pct": 0.01,
            "distance": 3,
            "lookback_period": 3,
            "top_patterns": 4
        },
        "medium": {
            "history_window": 90,
            "prominence_pct": 0.02,
            "distance": 7,
            "lookback_period": 5,
            "top_patterns": 5,
        },
        "long": {
            "history_window": 252,
            "prominence_pct": 0.04,
            "distance": 15,
            "lookback_period": 7,
            "top_patterns": 6
        }
    }
    
    def __init__(self, 
                 feature_df: pd.DataFrame, 
                 history_window: Optional[int] = None,
                 prominence_pct: Optional[float] = None,
                 distance: Optional[int] = None,
                 lookback_period: Optional[int] = None,
                 top_patterns: Optional[int] = None,
                 analysis_type: Literal['manual', 'short', 'medium', 'long'] = 'manual'):
        """
        Khởi tạo với DataFrame đã được làm giàu bởi FeatureEngine.

        Args:
            feature_df (pd.DataFrame): DataFrame chứa các đặc trưng.
            history_window (int): Số ngày lịch sử để các analyzer xem xét.
            prominence_pct (float): Ngưỡng độ nổi bật cho PatternRecognizer.
            distance (int): Khoảng cách tối thiểu giữa các đỉnh/đáy cho PatternRecognizer.
            lookback_period (int): Cửa số trong quá khứ để tính các Pattern
        """
        if not isinstance(feature_df, pd.DataFrame):
            raise ValueError(f"AnalysisEngine requires a non-empty pandas DataFrame with at least {history_window} rows.")
        if history_window is not None and len(feature_df) < history_window:
            raise ValueError(f"AnalysisEngine requires a non-empty pandas DataFrame with at least {history_window} rows.")
        if not isinstance(feature_df.index, pd.DatetimeIndex):
            raise TypeError("DataFrame index must be a DatetimeIndex for intraday analysis.")
        
        self.df = feature_df
        self.latest_row = self.df.iloc[-1]
        
        history_window, prominence_pct, distance, lookback_period, top_patterns = self._set_params(history_window,
                                                                                     prominence_pct,
                                                                                     distance,
                                                                                     lookback_period,
                                                                                     top_patterns,
                                                                                     analysis_type)
        
        # --- KHỞI TẠO TẤT CẢ CÁC CHUYÊN GIA ---
        # Truyền các tham số cấu hình xuống các lớp con tương ứng.
        self.trend_analyzer = DailyTrendAnalyzer(self.df)
        self.sr_identifier = DailySRIdentifier(self.df, history_window=history_window)
        self.pattern_recognizer = DailyPatternRecognizer(self.df, 
                                                        history_window=history_window,
                                                        prominence_pct=prominence_pct,
                                                        distance=distance,
                                                        lookback_period=lookback_period,
                                                        top_patterns=top_patterns)
        
    def _set_params(self,
                    history_window: Optional[int],
                    prominence_pct: Optional[float],
                    distance: Optional[int],
                    lookback_period: Optional[int],
                    top_pattenrs: Optional[int],
                    analysis_type: Literal['manual', 'short', 'medium', 'long'] = 'manual'):
        if analysis_type == 'manual':
            if history_window is None or prominence_pct is None or distance is None \
                or lookback_period is None or top_pattenrs is None:
                raise ValueError("Manual type requires some parameters.")
            return history_window, prominence_pct, distance, lookback_period, top_pattenrs

        # Nếu không phải manual, luôn lấy từ profile
        info(f"Using pre-defined parameters for '{analysis_type}' profile.")
        params = self.PARAMS_BY_PERIOD[analysis_type]
        return params['history_window'], params['prominence_pct'], params['distance'], \
            params['lookback_period'], params['top_patterns']

    def get_analysis_report(self) -> Dict[str, Any]:
        """
        Tạo báo cáo tình trạng kỹ thuật tổng hợp bằng cách gọi các chuyên gia.
        """
        info("Daily Analysis Engine: Generating Full Analysis Report ...")
        
        # --- GỌI CÁC CHUYÊN GIA ĐỂ LẤY KẾT QUẢ PHÂN TÍCH ---
        info("Trend Analyzer: Analyzing Trend ...")
        trend_report = self.trend_analyzer.analyze_trend()
        
        info("Support Resistance Identifier: Identifing levels ...")
        sr_report = self.sr_identifier.identify_levels()
        
        info("Pattern Recoginizer: Finding patterns ...")
        patterns_report = self.pattern_recognizer.find_patterns() # Thay thế placeholder

        # --- NÂNG CẤP TRONG TƯƠNG LAI (v2) ---
        # Có thể truyền kết quả của recognizer vào sr_identifier để có S/R chính xác hơn
        # sr_report_v2 = self.sr_identifier.identify_levels_v2(self.pattern_recognizer)

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
        indicators_to_extract = [
            'SMA_20', 'SMA_50', 'SMA_200', 
            'RSI_14', 'ADX_14', 'DMP_14', 'DMN_14',
            'BBU_20_2.0', 'BBL_20_2.0', 'ATRr_14', 'PSARs_0.02_0.2'
        ]
        
        info("Daily Analysis Engine: Extracting key indicators for multi-timeframe analysis...")
        key_indicators = {}
        for indicator in indicators_to_extract:
            # Chuyển tên cột sang chữ thường để tìm kiếm nhất quán
            indicator_lower = indicator.lower()
            if indicator_lower in self.latest_row.index and pd.notna(self.latest_row[indicator_lower]):
                key_indicators[indicator] = round(self.latest_row[indicator_lower], 2)
            else:
                # Thử tìm với tên gốc (viết hoa) phòng trường hợp FeatureEngine thay đổi
                if indicator in self.latest_row.index and pd.notna(self.latest_row[indicator]):
                    key_indicators[indicator] = round(self.latest_row[indicator], 2)
                else:
                    key_indicators[indicator] = None
                
        return key_indicators