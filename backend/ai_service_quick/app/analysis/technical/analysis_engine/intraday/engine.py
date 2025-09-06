"""Intraday technical analysis engine for coordinating various intraday analysis components."""

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
    """Facade that analyzes feature-enriched intraday DataFrame and generates reports.
    
    It coordinates intraday analysis experts.
    """
    
    def __init__(self, feature_df: pd.DataFrame):
        """Initialize with a feature-enriched DataFrame.
        
        Args:
            feature_df (pd.DataFrame): DataFrame with technical features for intraday analysis
            
        Raises:
            ValueError: If feature_df is not a valid DataFrame or is empty
            TypeError: If DataFrame index is not a DatetimeIndex
        """
        if not isinstance(feature_df, pd.DataFrame) or feature_df.empty:
            raise ValueError("IntradayAnalysisEngine requires a non-empty pandas DataFrame.")
        if not isinstance(feature_df.index, pd.DatetimeIndex):
            raise TypeError("DataFrame index must be a DatetimeIndex for intraday analysis.")

        self.df = feature_df
        self.latest_row = self.df.iloc[-1]

        # Initialize intraday experts
        self.status_analyzer = IntradayStatusAnalyzer(self.df)
        self.level_identifier = IntradayLevelIdentifier(self.df)
        self.momentum_analyzer = IntradayMomentumAnalyzer(self.df)

    def get_analysis_report(self) -> IntradayAnalysisReport:
        """Generate a comprehensive intraday analysis report.
        
        Returns:
            IntradayAnalysisReport: Complete intraday analysis report
        """
        logger.info("Generating Intraday Report ---")
        
        logger.info("Status Analyzer: Analyzing current status ...")
        current_status = self.status_analyzer.analyze_current_status()
        
        logger.info("Level Identifier: Identifying key levels ...")
        key_levels = self.level_identifier.identify_key_levels()
        
        logger.info("Momentum Analyzer: Analyzing momentum and volume ...")
        momentum = self.momentum_analyzer.analyze_momentum_and_volume()
        
        return IntradayAnalysisReport(
            current_status_report=current_status,
            key_levels=key_levels,
            momentum_report=momentum
        )
        
    @staticmethod
    def get_mock_report(daily_ohlcv: pd.Series) -> IntradayAnalysisReport:
        """Generate a mock intraday report from daily OHLCV data.
        
        Args:
            daily_ohlcv (pd.Series): Daily OHLCV data series
            
        Returns:
            IntradayAnalysisReport: Mock intraday analysis report
        """
        # === 1. Create KeyLevelsReport ===
        # This is the easiest part because we can derive directly from the daily candle.
        key_levels = KeyLevelsReport(
            day_high=daily_ohlcv['high'],
            day_low=daily_ohlcv['low'],
            open_price=daily_ohlcv['open'],
            vwap=None,            # Cannot know intraday VWAP, set to None (undefined).
            or_30m_high=None,     # No 30-minute opening data, set to None.
            or_30m_low=None       # No 30-minute opening data, set to None.
        )

        # === 2. Create CurrentStatusReport ===
        # Assume the day's close price is the "current price" for comparison.
        current_status = CurrentStatusReport(
            vwap_status='undefined', # Since VWAP is undefined.
            open_status='above' if daily_ohlcv['close'] >= daily_ohlcv['open'] else 'below',
            rsi_status='neutral',    # Assume neutral intraday RSI (50).
            evidence={
                "mock_reason": "Data simulated from daily candle.",
                "last_price": daily_ohlcv['close'],
                "open_price": daily_ohlcv['open'],
                "rsi": 50.0
            }
        )
        
        # === 3. Create MomentumReport ===
        # Choose the safest values, without creating strong signals.
        momentum = MomentumReport(
            macd_crossover='neutral', # No MACD crossover signal.
            volume_status='normal',   # Assume no volume spikes during the day.
            opening_range_status='inside', # Assume price remains within opening range.
            evidence={
                "mock_reason": "Data simulated from daily candle.",
                "volume_ratio": 1.0, # Average volume ratio.
                "macd_signal_status": "No intraday data for comparison."
            }
        )

        # === 4. Assemble final report ===
        mock_report = IntradayAnalysisReport(
            current_status_report=current_status,
            momentum_report=momentum,
            key_levels=key_levels
        )
        
        return mock_report
            