import pandas as pd
from typing import Dict, Any

from .status_analyzer import IntradayStatusAnalyzer
from .level_identifier import IntradayLevelIdentifier
from .momentum_analyzer import IntradayMomentumAnalyzer

from itapia_common.schemas.entities.analysis.technical import IntradayAnalysisReport
from itapia_common.schemas.entities.analysis.technical.intraday import KeyLevelsReport, CurrentStatusReport, MomentumReport
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Intraday Analysis Engine')

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

    def get_analysis_report(self):
        """
        Tạo báo cáo phân tích intraday tổng hợp.
        """
        logger.info("Generating Intraday Report ---")
        
        logger.info("Status Analyzer: Analyzing current status ...")
        current_status = self.status_analyzer.analyze_current_status()
        
        logger.info("Level Identifier: Identifing key levels ...")
        key_levels = self.level_identifier.identify_key_levels()
        
        logger.info("Momentum Analyzer: Analyzing momentum and volume ...")
        momentum = self.momentum_analyzer.analyze_momentum_and_volume()
        
        return IntradayAnalysisReport(
            current_status_report=current_status,
            key_levels=key_levels,
            momentum_report=momentum
        )
        
    @staticmethod
    def get_mock_report(daily_ohlcv: pd.Series):
        # === 1. Tạo KeyLevelsReport ===
        # Đây là phần dễ nhất vì chúng ta có thể suy ra trực tiếp từ nến ngày.
        key_levels = KeyLevelsReport(
            day_high=daily_ohlcv['high'],
            day_low=daily_ohlcv['low'],
            open_price=daily_ohlcv['open'],
            vwap=None,            # Không thể biết VWAP trong ngày, để là None (undefined).
            or_30m_high=None,     # Không có dữ liệu 30 phút đầu, để là None.
            or_30m_low=None       # Không có dữ liệu 30 phút đầu, để là None.
        )

        # === 2. Tạo CurrentStatusReport ===
        # Giả định giá đóng cửa của ngày là "giá hiện tại" để so sánh.
        current_status = CurrentStatusReport(
            vwap_status='undefined', # Vì VWAP không xác định.
            open_status='above' if daily_ohlcv['close'] >= daily_ohlcv['open'] else 'below',
            rsi_status='neutral',    # Giả định RSI trong ngày là trung tính (50).
            evidence={
                "mock_reason": "Data simulated from daily candle.",
                "last_price": daily_ohlcv['close'],
                "open_price": daily_ohlcv['open'],
                "rsi": 50.0
            }
        )
        
        # === 3. Tạo MomentumReport ===
        # Chọn các giá trị an toàn nhất, không tạo ra tín hiệu mạnh.
        momentum = MomentumReport(
            macd_crossover='neutral', # Không có tín hiệu giao cắt MACD.
            volume_status='normal',   # Giả định không có đột biến volume trong ngày.
            opening_range_status='inside', # Giả định giá vẫn nằm trong vùng mở cửa.
            evidence={
                "mock_reason": "Data simulated from daily candle.",
                "volume_ratio": 1.0, # Tỷ lệ volume trung bình.
                "macd_signal_status": "No intraday data for comparison."
            }
        )

        # === 4. Lắp ráp báo cáo cuối cùng ===
        mock_report = IntradayAnalysisReport(
            current_status_report=current_status,
            momentum_report=momentum,
            key_levels=key_levels
        )
        
        return mock_report
            