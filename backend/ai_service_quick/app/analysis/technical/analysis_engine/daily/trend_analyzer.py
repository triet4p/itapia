"""Daily trend analysis engine for identifying market trends across multiple timeframes."""

import pandas as pd

from itapia_common.schemas.entities.analysis.technical.daily import MidTermTrendReport, \
    LongTermTrendReport, OverallStrengthTrendReport, TrendReport


class DailyTrendAnalyzer:
    """Analyzes market trends using multiple technical indicators and timeframes."""
    
    def __init__(self, feature_df: pd.DataFrame):
        """Initialize the trend analyzer with feature data.
        
        Args:
            feature_df (pd.DataFrame): DataFrame with technical features
            
        Raises:
            ValueError: If feature_df is empty
        """
        if feature_df.empty:
            raise ValueError("Input DataFrame for TrendAnalyzer cannot be empty.")
        
        self.df = feature_df
        self.latest_row = self.df.iloc[-1]
        
    def _analyze_ma_trend(self, short_ma_col: str, long_ma_col: str) -> str:
        """Analyze trend based on moving average relationship.
        
        Args:
            short_ma_col (str): Column name for shorter-term moving average
            long_ma_col (str): Column name for longer-term moving average
            
        Returns:
            str: Trend direction ('uptrend', 'downtrend', or 'undefined')
        """
        if short_ma_col not in self.latest_row or long_ma_col not in self.latest_row:
            return "undefined"
        
        if self.latest_row[short_ma_col] > self.latest_row[long_ma_col]:
            return "uptrend"
        else:
            return "downtrend"
        
    def _get_adx_strength(self, adx_col: str) -> OverallStrengthTrendReport:
        """Get trend strength based on ADX indicator.
        
        Args:
            adx_col (str): Column name for ADX values
            
        Returns:
            OverallStrengthTrendReport: Trend strength report
        """
        if adx_col not in self.latest_row:
            return OverallStrengthTrendReport(
                strength='undefined',
                value=0
            )
        
        adx_val = self.latest_row[adx_col]
        if adx_val > 25:
            return OverallStrengthTrendReport(
                strength='strong', 
                value=adx_val
            )
        elif adx_val >= 20:
            return OverallStrengthTrendReport(
                strength='moderate', 
                value=adx_val
            )
        else:
            return OverallStrengthTrendReport(
                strength='weak', 
                value=adx_val
            )
        
    def _get_adx_direction(self, dmp_col: str, dmn_col: str) -> str:
        """Get trend direction based on ADX directional indicators.
        
        Args:
            dmp_col (str): Column name for +DI values
            dmn_col (str): Column name for -DI values
            
        Returns:
            str: Trend direction ('uptrend', 'downtrend', or 'undefined')
        """
        if dmp_col not in self.latest_row or dmn_col not in self.latest_row: 
            return "undefined"
        return "uptrend" if self.latest_row[dmp_col] > self.latest_row[dmn_col] else "downtrend"
    
    def _get_mid_term_view(self) -> MidTermTrendReport:
        """Get mid-term trend analysis (20/50 moving averages).
        
        Returns:
            MidTermTrendReport: Mid-term trend analysis report
        """
        # Appropriate MA pair for medium term 20/50
        short_ma = 'SMA_20'
        long_ma = 'SMA_50'
        trend_direction = self._analyze_ma_trend(short_ma, long_ma)
        
        evidence = {
            "short_ma_name": short_ma,
            "short_ma_value": round(self.latest_row.get(short_ma, 0), 2),
            "long_ma_name": long_ma,
            "long_ma_value": round(self.latest_row.get(long_ma, 0), 2)
        }
        
        # Check price position relative to medium-term MA
        ma_status = "undefined"
        if 'close' in self.latest_row and 'SMA_50' in self.latest_row:
            if self.latest_row['close'] > self.latest_row['SMA_50']:
                ma_status = "positive"  # Positive
            else:
                ma_status = "negative"  # Under pressure
        
        # Analyze ADX to see current direction
        adx_direction = self._get_adx_direction('DMP_14', 'DMN_14')

        return MidTermTrendReport(
            ma_direction=trend_direction,
            ma_status=ma_status,
            adx_direction=adx_direction,
            evidence=evidence
        )
    
    def _get_long_term_view(self) -> LongTermTrendReport:
        """Analyze long-term trend (several months to a year).
        
        Returns:
            LongTermTrendReport: Long-term trend analysis report
        """
        # Classic MA pair 50/200
        short_ma = 'SMA_50'
        long_ma = 'SMA_200'
        trend_direction = self._analyze_ma_trend(short_ma, long_ma)
        
        evidence = {
            "short_ma_name": short_ma,
            "short_ma_value": round(self.latest_row.get(short_ma, 0), 2),
            "long_ma_name": long_ma,
            "long_ma_value": round(self.latest_row.get(long_ma, 0), 2)
        }
        
        # Check price position relative to long-term MA
        status = "Undefined"
        if 'close' in self.latest_row and 'SMA_200' in self.latest_row:
            if self.latest_row['close'] > self.latest_row['SMA_200']:
                status = "positive"
            else:
                status = "negative"

        return LongTermTrendReport(
            ma_direction=trend_direction,
            ma_status=status,
            evidence=evidence
        )
    
    def analyze_trend(self) -> TrendReport:
        """Perform comprehensive trend analysis and return a multidimensional dictionary.
        
        Returns:
            TrendReport: Complete trend analysis report
        """
        # Analyze each timeframe independently
        long_term_analysis = self._get_long_term_view()
        mid_term_analysis = self._get_mid_term_view()
        
        # Overall trend strength measured by standard ADX(14)
        adx_strength = self._get_adx_strength('ADX_14')
        
        # --- Synthesis Logic ---
        # "Primary" trend is defined as mid-term trend,
        # because that is the main focus of the project.
        # However, the report still contains complete long-term information.
        
        return TrendReport(
            primary_focus='mid-term',
            midterm_report=mid_term_analysis,
            longterm_report=long_term_analysis,
            overall_strength=adx_strength
        )
        
