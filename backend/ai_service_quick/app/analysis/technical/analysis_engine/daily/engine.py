"""Daily technical analysis engine for coordinating various technical analysis components."""

from typing import Literal, Optional

import pandas as pd
from itapia_common.logger import ITAPIALogger
from itapia_common.schemas.entities.analysis.technical import DailyAnalysisReport
from itapia_common.schemas.entities.analysis.technical.daily import KeyIndicators

from .pattern_recognizer import DailyPatternRecognizer
from .sr_identifier import DailySRIdentifier
from .trend_analyzer import DailyTrendAnalyzer

logger = ITAPIALogger("Daily Analysis Engine")


class DailyAnalysisEngine:
    """Facade that coordinates daily technical analysis experts.

    This class receives a feature-enriched DataFrame and coordinates the subordinate analyzers
    (Trend, Support/Resistance, Pattern) to create a comprehensive technical analysis report.
    It allows customization of "analysis style" (short, medium, long) by passing different
    parameter sets to the subordinate classes.
    """

    PARAMS_BY_PERIOD = {
        "short": {
            "history_window": 30,
            "prominence_pct": 0.01,
            "distance": 3,
            "lookback_period": 3,
            "top_patterns": 4,
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
            "top_patterns": 6,
        },
    }

    def __init__(
        self,
        feature_df: pd.DataFrame,
        history_window: Optional[int] = None,
        prominence_pct: Optional[float] = None,
        distance: Optional[int] = None,
        lookback_period: Optional[int] = None,
        top_patterns: Optional[int] = None,
        analysis_type: Literal["manual", "short", "medium", "long"] = "manual",
    ):
        """Initialize with a DataFrame enriched by FeatureEngine.

        Args:
            feature_df (pd.DataFrame): DataFrame containing technical features
            history_window (int, optional): Number of historical days for analyzers to consider
            prominence_pct (float, optional): Prominence threshold for PatternRecognizer
            distance (int, optional): Minimum distance between peaks/troughs for PatternRecognizer
            lookback_period (int, optional): Lookback window in the past to calculate patterns
            top_patterns (int, optional): Number of top patterns to identify
            analysis_type (Literal['manual', 'short', 'medium', 'long']): Analysis profile type

        Raises:
            ValueError: If feature_df is not a valid DataFrame or has insufficient data
            TypeError: If DataFrame index is not a DatetimeIndex
        """
        if not isinstance(feature_df, pd.DataFrame):
            raise ValueError(
                f"AnalysisEngine requires a non-empty pandas DataFrame with at least {history_window} rows."
            )
        if history_window is not None and len(feature_df) < history_window:
            raise ValueError(
                f"AnalysisEngine requires a non-empty pandas DataFrame with at least {history_window} rows."
            )
        if not isinstance(feature_df.index, pd.DatetimeIndex):
            raise TypeError(
                "DataFrame index must be a DatetimeIndex for intraday analysis."
            )

        self.df = feature_df
        self.latest_row = self.df.iloc[-1]

        history_window, prominence_pct, distance, lookback_period, top_patterns = (
            self._set_params(
                history_window,
                prominence_pct,
                distance,
                lookback_period,
                top_patterns,
                analysis_type,
            )
        )

        # --- INITIALIZE ALL EXPERTS ---
        # Pass configuration parameters to corresponding subordinate classes
        self.trend_analyzer = DailyTrendAnalyzer(self.df)
        self.sr_identifier = DailySRIdentifier(self.df, history_window=history_window)
        self.pattern_recognizer = DailyPatternRecognizer(
            self.df,
            history_window=history_window,
            prominence_pct=prominence_pct,
            distance=distance,
            lookback_period=lookback_period,
            top_patterns=top_patterns,
        )

    def _set_params(
        self,
        history_window: Optional[int],
        prominence_pct: Optional[float],
        distance: Optional[int],
        lookback_period: Optional[int],
        top_patterns: Optional[int],
        analysis_type: Literal["manual", "short", "medium", "long"] = "manual",
    ) -> tuple:
        """Set parameters based on analysis type.

        Args:
            history_window (int, optional): Number of historical days to analyze
            prominence_pct (float, optional): Prominence threshold for pattern recognition
            distance (int, optional): Minimum distance between peaks/troughs
            lookback_period (int, optional): Lookback period for pattern analysis
            top_patterns (int, optional): Number of top patterns to identify
            analysis_type (Literal): Analysis profile type

        Returns:
            tuple: Tuple of (history_window, prominence_pct, distance, lookback_period, top_patterns)

        Raises:
            ValueError: If manual type is specified but required parameters are missing
        """
        if analysis_type == "manual":
            if (
                history_window is None
                or prominence_pct is None
                or distance is None
                or lookback_period is None
                or top_patterns is None
            ):
                raise ValueError("Manual type requires all parameters to be specified.")
            return (
                history_window,
                prominence_pct,
                distance,
                lookback_period,
                top_patterns,
            )

        # If not manual, always get from profile
        logger.info(f"Using pre-defined parameters for '{analysis_type}' profile.")
        params = self.PARAMS_BY_PERIOD[analysis_type]
        return (
            params["history_window"],
            params["prominence_pct"],
            params["distance"],
            params["lookback_period"],
            params["top_patterns"],
        )

    def get_analysis_report(self) -> DailyAnalysisReport:
        """Generate a comprehensive technical analysis report by calling the experts.

        Returns:
            DailyAnalysisReport: Complete daily technical analysis report
        """
        logger.info("Generating Full Analysis Report ...")

        # --- CALL EXPERTS TO GET ANALYSIS RESULTS ---
        logger.info("Trend Analyzer: Analyzing Trend ...")
        trend_report = self.trend_analyzer.analyze_trend()

        logger.info("Support Resistance Identifier: Identifying levels ...")
        sr_report = self.sr_identifier.identify_levels()

        logger.info("Pattern Recognizer: Finding patterns ...")
        patterns_report = self.pattern_recognizer.find_patterns()  # Replace placeholder
        logger.info("Success")

        # --- FUTURE ENHANCEMENT (v2) ---
        # Could pass recognizer results to sr_identifier for more accurate S/R levels
        # sr_report_v2 = self.sr_identifier.identify_levels_v2(self.pattern_recognizer)

        # --- COMPILE INTO FINAL REPORT ---
        return DailyAnalysisReport(
            key_indicators=self._extract_key_indicators(),
            trend_report=trend_report,
            sr_report=sr_report,
            pattern_report=patterns_report,
        )

    def _extract_key_indicators(self) -> KeyIndicators:
        """Extract key indicator values to support both medium and long-term analysis.

        Returns:
            KeyIndicators: Object containing key technical indicator values
        """
        indicators_to_extract = [
            "SMA_20",
            "SMA_50",
            "SMA_200",
            "RSI_14",
            "ADX_14",
            "DMP_14",
            "DMN_14",
            "BBU_20_2.0",
            "BBL_20_2.0",
            "ATRr_14",
            "PSARs_0.02_0.2",
        ]

        logger.info("Extracting key indicators for multi-timeframe analysis...")
        key_indicators = {}
        for indicator in indicators_to_extract:
            # Convert column name to lowercase for consistent search
            indicator_lower = indicator.lower()
            if indicator_lower in self.latest_row.index and pd.notna(
                self.latest_row[indicator_lower]
            ):
                key_indicators[indicator] = round(self.latest_row[indicator_lower], 2)
            else:
                # Try with original name (uppercase) in case FeatureEngine changes
                if indicator in self.latest_row.index and pd.notna(
                    self.latest_row[indicator]
                ):
                    key_indicators[indicator] = round(self.latest_row[indicator], 2)
                else:
                    key_indicators[indicator] = None

        return KeyIndicators(
            sma_20=key_indicators["SMA_20"],
            sma_50=key_indicators["SMA_50"],
            sma_200=key_indicators["SMA_200"],
            rsi_14=key_indicators["RSI_14"],
            adx_14=key_indicators["ADX_14"],
            dmp_14=key_indicators["DMP_14"],
            dmn_14=key_indicators["DMN_14"],
            bbu_20=key_indicators["BBU_20_2.0"],
            bbl_20=key_indicators["BBL_20_2.0"],
            atr_14=key_indicators["ATRr_14"],
            psar=key_indicators["PSARs_0.02_0.2"],
        )
