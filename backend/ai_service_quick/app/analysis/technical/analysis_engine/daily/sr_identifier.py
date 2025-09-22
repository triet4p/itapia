"""Daily support and resistance identification engine."""

from typing import Any, List

import pandas as pd
from itapia_common.schemas.entities.analysis.technical.daily import (
    SRIdentifyLevelObj,
    SRReport,
)


class DailySRIdentifier:
    """Expert for identifying Support and Resistance levels.

    Version 1 (v1) focuses on methods that do not depend on PatternRecognizer.
    """

    def __init__(self, feature_df: pd.DataFrame, history_window: int = 90):
        """Initialize with a feature-enriched DataFrame.

        Args:
            feature_df (pd.DataFrame): DataFrame from FeatureEngine
            history_window (int): Number of historical days to consider for analysis

        Raises:
            ValueError: If feature_df is empty or has insufficient data
        """
        if feature_df.empty or len(feature_df) < history_window:
            raise ValueError(
                f"Input DataFrame must not be empty and have at least {history_window} rows."
            )

        self.df = feature_df
        # Get a data window for analysis
        self.analysis_df = self.df.tail(history_window).copy()
        self.latest_row = self.analysis_df.iloc[-1]
        self.current_price = self.latest_row["close"]

        self.history_window = history_window

    def identify_levels(self) -> SRReport:
        """Main function that aggregates S/R levels from multiple methods.

        Returns:
            SRReport: Report containing identified support and resistance levels
        """

        all_levels_with_source: List[SRIdentifyLevelObj] = []
        all_levels_with_source.extend(self._get_dynamic_levels_from_ma_bb())
        all_levels_with_source.extend(self._get_pivot_point_levels())
        all_levels_with_source.extend(self._get_simple_fibonacci_levels())

        support_objects: List[SRIdentifyLevelObj] = []
        resistance_objects: List[SRIdentifyLevelObj] = []

        for sr_level_obj in all_levels_with_source:
            if sr_level_obj.level < self.current_price:
                support_objects.append(sr_level_obj)
            else:
                resistance_objects.append(sr_level_obj)

        return SRReport(
            history_window=self.history_window,
            supports=sorted(support_objects, key=lambda x: x.level, reverse=True),
            resistances=sorted(resistance_objects, key=lambda x: x.level),
        )

    # --- VERSION 1 METHODS ---

    def _get_dynamic_levels_from_ma_bb(self) -> List[SRIdentifyLevelObj]:
        """Get dynamic S/R levels from Moving Averages and Bollinger Bands.

        These are levels that change daily.

        Returns:
            List[SRIdentifyLevelObj]: List of dynamic support/resistance levels
        """
        levels = []
        # Columns to extract from the last data row
        dynamic_level_cols = [
            "SMA_20",
            "SMA_50",
            "SMA_200",
            "BBU_20_2.0",
            "BBL_20_2.0",
            "BBM_20_2.0",
        ]

        for col in dynamic_level_cols:
            if col in self.latest_row and pd.notna(self.latest_row[col]):
                levels.append(
                    SRIdentifyLevelObj(level=round(self.latest_row[col], 2), source=col)
                )

        return levels

    def _get_pivot_point_levels(self) -> List[SRIdentifyLevelObj]:
        """Calculate classic Pivot Points based on the previous day's data.

        Returns:
            List[SRIdentifyLevelObj]: List of pivot point levels
        """
        if len(self.analysis_df) < 2:
            return []

        prev_row = self.analysis_df.iloc[-2]
        H, L, C = prev_row["high"], prev_row["low"], prev_row["close"]

        PP = (H + L + C) / 3
        R1 = (2 * PP) - L
        S1 = (2 * PP) - H
        R2 = PP + (H - L)
        S2 = PP - (H - L)
        R3 = H + 2 * (PP - L)
        S3 = L - 2 * (H - PP)

        names = [f"Pivot point {x}" for x in ["PP", "R1", "S1", "R2", "S2", "R3", "S3"]]
        vals = [PP, R1, S1, R2, S2, R3, S3]

        levels = []
        for i in range(len(vals)):
            levels.append(SRIdentifyLevelObj(level=round(vals[i], 2), source=names[i]))

        return levels

    def _get_simple_fibonacci_levels(self) -> List[SRIdentifyLevelObj]:
        """Version 1: Calculate Fibonacci Retracement levels based on
        the highest and lowest points in the analysis window.

        Returns:
            List[SRIdentifyLevelObj]: List of Fibonacci retracement levels
        """
        # Identify the "wave" in a simple way
        swing_high = self.analysis_df["high"].max()
        swing_low = self.analysis_df["low"].min()

        price_range = swing_high - swing_low
        if price_range == 0:
            return []

        # Classic Fibonacci ratios
        fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]

        levels = []
        # Assume an uptrend (calculate support levels)
        for ratio in fib_ratios:
            levels.append(
                SRIdentifyLevelObj(
                    level=round(swing_high - price_range * ratio, 2),
                    source=f"Fibonacci Ratio {ratio:.4f}",
                )
            )

            # Also add extension levels (could be resistance)
            levels.append(
                SRIdentifyLevelObj(
                    level=round(swing_high + price_range * ratio, 2),
                    source=f"Fibonacci Ratio {-ratio:.4f}",
                )
            )

        return levels

    # --- PLACEHOLDER METHODS FOR VERSION 2 ---

    def _get_levels_from_extrema_v2(
        self, recognizer: Any = None
    ) -> List[SRIdentifyLevelObj]:
        """Version 2: Will get static S/R levels from historical peaks/troughs
        provided by PatternRecognizer.

        Args:
            recognizer: An instance of PatternRecognizer

        Returns:
            List[SRIdentifyLevelObj]: List of S/R levels from extrema
        """
        # In version 1, this function does nothing.
        # It is a placeholder for future enhancement.

        # --- EXAMPLE CODE THAT WILL BE IN VERSION 2 ---
        # if recognizer is None:
        #     return []
        #
        # # Get peaks and troughs from recognizer
        # peaks = recognizer.peaks
        # troughs = recognizer.troughs
        #
        # # Price levels of peaks/troughs are the S/R levels
        # peak_prices = peaks['price'].tolist()
        # trough_prices = troughs['price'].tolist()
        #
        # return peak_prices + trough_prices

        return []  # Return empty list in v1

    def _get_advanced_fibonacci_levels_v2(
        self, recognizer: Any = None
    ) -> List[SRIdentifyLevelObj]:
        """Version 2: Will calculate Fibonacci based on important peaks/troughs
        rather than just min/max.

        Args:
            recognizer: An instance of PatternRecognizer

        Returns:
            List[SRIdentifyLevelObj]: List of advanced Fibonacci levels
        """
        # Placeholder for version 2
        return []
