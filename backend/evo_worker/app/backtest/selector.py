"""Backtest point selector for identifying significant dates for backtesting."""

from datetime import datetime, timezone
from typing import Dict, List, Set

import pandas as pd
from app.backtest.data_prepare import BacktestDataPreparer
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger("Backtest Point Selector")


class BacktestPointSelector:
    """An intelligent class to select "special" dates worthy of backtesting from
    historical OHLCV data, using Pandas-based calculations without TA-Lib dependency.

    Supports method chaining to build a set of backtest points.
    """

    DEFAULT_CONFIG = {
        "volatility_quantile": 0.95,
        "recency_weight": 0.5,
    }

    def __init__(
        self, ticker: str, data_preparer: BacktestDataPreparer, config: Dict = None
    ):
        """Initialize selector with OHLCV DataFrame.

        Args:
            ohlcv_df (pd.DataFrame): DataFrame containing historical price data,
                                     must have DatetimeIndex and columns 'open', 'high', 'low', 'close'.
            config (Dict, optional): A dictionary to fine-tune parameters.
        """

        ohlcv_df = data_preparer.get_daily_ohlcv_for_ticker(ticker, limit=5000)

        if ohlcv_df.empty:
            raise ValueError("OHLCV DataFrame cannot be empty.")

        self.config = config or self.DEFAULT_CONFIG

        self.df = ohlcv_df.copy()

        # 1. Prepare data and indicators ONCE
        self._calculate_indicators()

        # 2. Use a Set to store selected points, automatically handling duplicates
        self.selected_points: Set[pd.Timestamp] = set()

    def _calculate_indicators(self):
        """Calculate all required indicators to detect events using Pandas."""
        logger.info("Calculating base indicators for point selection using Pandas...")

        # Calculate RSI using Pandas
        delta = self.df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.df["rsi"] = 100 - (100 / (1 + rs))

        # Calculate SMA using Pandas
        self.df["sma_50"] = self.df["close"].rolling(window=50).mean()
        self.df["sma_200"] = self.df["close"].rolling(window=200).mean()

        # Calculate % daily price change
        self.df["daily_change_pct"] = self.df["close"].pct_change().abs() * 100

        # Remove rows with NaN created by indicators (mainly due to SMA_200)
        self.df.dropna(inplace=True)

    def add_monthly_points(
        self,
        day_of_month: int,
        max_points: int = 100,
        selector_start: datetime | None = None,
        selector_end: datetime | None = None,
    ) -> "BacktestPointSelector":
        """Add periodic monthly backtest points, prioritizing recent dates.

        Args:
            day_of_month (int): Day of month to target.
            max_points (int): Maximum number of periodic points to fetch.
        """
        logger.info(
            f"Adding up to {max_points} monthly points on day {day_of_month}, prioritizing recent dates..."
        )

        selector_start = (
            selector_start.replace(tzinfo=timezone.utc)
            if selector_start
            else self.df.index.min().to_pydatetime()
        )
        selector_end = (
            selector_end.replace(tzinfo=timezone.utc)
            if selector_end
            else self.df.index.max().to_pydatetime()
        )

        # --- STEP 1: CREATE ALL PERIODIC CANDIDATE DATES ---

        candidate_target_dates: List[pd.Timestamp] = []
        # Iterate through all months in the time range
        for month_start_date in pd.date_range(
            start=selector_start, end=selector_end, freq="MS"
        ):
            # Handle case where date doesn't exist (e.g., Feb 31)
            day = min(day_of_month, month_start_date.days_in_month)
            target_date = month_start_date.replace(day=day)
            candidate_target_dates.append(target_date)

        # Sort candidate dates in DESCENDING order (from most recent to oldest)
        candidate_target_dates.sort(reverse=True)

        # --- STEP 2: FIND ACTUAL TRADING DATES NEAREST AND FILTER ---

        target_dates_to_find = pd.to_datetime(
            candidate_target_dates[:max_points], utc=True
        )

        # --- STEP 2: FIND NEAREST ACTUAL TRADING DATES ---

        # FIX ERROR HERE: Use get_indexer instead of get_loc
        # get_indexer takes a list of dates and returns a list of positions
        indices = self.df.index.get_indexer(target_dates_to_find, method="ffill")

        # Filter out valid positions (not -1) and remove duplicates
        valid_indices = sorted(list(set(idx for idx in indices if idx != -1)))

        # Get actual dates from valid positions
        points_to_add = self.df.index[valid_indices]

        # --- STEP 3: UPDATE MAIN POINT SET ---

        self.selected_points.update(points_to_add)

        return self

    def add_significant_points(
        self,
        max_points: int = 100,
        selector_start: datetime | None = None,
        selector_end: datetime | None = None,
    ) -> "BacktestPointSelector":
        """Add "special" backtest points based on technical events.

        Args:
            max_points (int, optional): Maximum number of significant points to add. Defaults to 100.
            selector_start (datetime | None, optional): Start date for selection. Defaults to None.
            selector_end (datetime | None, optional): End date for selection. Defaults to None.

        Returns:
            BacktestPointSelector: Self for method chaining
        """
        logger.info(f"Adding up to {max_points} significant points...")
        volatility_points = self._find_volatility_spikes()
        trend_change_points = self._find_trend_changes()
        momentum_points = self._find_momentum_extremes()

        all_candidates = pd.concat(
            [volatility_points, trend_change_points, momentum_points]
        )
        if all_candidates.empty:
            logger.warn("No significant points found.")
            return self

        all_candidates.sort_values(by="event_score", ascending=False, inplace=True)
        distinct_candidates = all_candidates.drop_duplicates(
            subset=["date"], keep="first"
        ).copy()

        self._apply_recency_bias(distinct_candidates)

        top_points = distinct_candidates.sort_values(
            by="final_score", ascending=False
        ).head(max_points)

        selector_start = (
            selector_start.replace(tzinfo=timezone.utc)
            if selector_start
            else self.df.index.min().to_pydatetime()
        )
        selector_end = (
            selector_end.replace(tzinfo=timezone.utc)
            if selector_end
            else self.df.index.max().to_pydatetime()
        )

        for point in top_points["date"]:
            if point.to_pydatetime() > selector_end:
                continue
            if point.to_pydatetime() < selector_start:
                continue
            self.selected_points.add(point)

        return self

    def get_points(self) -> List[datetime]:
        """Return the final list of selected backtest points, sorted.

        Returns:
            List[datetime]: Sorted list of selected backtest dates
        """
        if not self.selected_points:
            return []
        return sorted([ts.to_pydatetime() for ts in self.selected_points])

    def get_points_as_timestamps(self) -> List[int]:
        """Return the final list of selected backtest points as Unix timestamps (integer), sorted.
        Very useful for sending through APIs.

        Returns:
            List[int]: Sorted list of Unix timestamps
        """
        if not self.selected_points:
            return []
        # Convert to integer timestamp and sort
        return sorted([int(ts.timestamp()) for ts in self.selected_points])

    # --- HELPER METHODS (PRIVATE) ---
    def _find_volatility_spikes(self) -> pd.DataFrame:
        """Find dates with significant volatility spikes.

        Returns:
            pd.DataFrame: DataFrame with volatility spike dates and scores
        """
        quantile = self.config.get("volatility_quantile", 0.95)
        spike_threshold = self.df["daily_change_pct"].quantile(quantile)
        spikes = self.df[self.df["daily_change_pct"] >= spike_threshold]
        return pd.DataFrame({"date": spikes.index, "event_score": 0.7})

    def _find_trend_changes(self) -> pd.DataFrame:
        """Find dates with trend changes (Golden/Death crosses).

        Returns:
            pd.DataFrame: DataFrame with trend change dates and scores
        """
        df = self.df
        golden_cross = (df["sma_50"] > df["sma_200"]) & (
            df["sma_50"].shift(1) <= df["sma_200"].shift(1)
        )
        death_cross = (df["sma_50"] < df["sma_200"]) & (
            df["sma_50"].shift(1) >= df["sma_200"].shift(1)
        )
        crosses = df[golden_cross | death_cross]
        return pd.DataFrame({"date": crosses.index, "event_score": 1.0})

    def _find_momentum_extremes(self) -> pd.DataFrame:
        """Find dates with momentum extremes (RSI overbought/oversold).

        Returns:
            pd.DataFrame: DataFrame with momentum extreme dates and scores
        """
        df = self.df
        overbought = (df["rsi"] > 70) & (df["rsi"].shift(1) <= 70)
        oversold = (df["rsi"] < 30) & (df["rsi"].shift(1) >= 30)
        extremes = df[overbought | oversold]
        return pd.DataFrame({"date": extremes.index, "event_score": 0.8})

    def _apply_recency_bias(self, candidates_df: pd.DataFrame):
        """Apply recency bias to candidate points to favor recent events.

        Args:
            candidates_df (pd.DataFrame): DataFrame with candidate dates and scores
        """
        recency_weight = self.config.get("recency_weight", 0.5)
        min_date = candidates_df["date"].min()
        max_date = candidates_df["date"].max()

        if max_date == min_date:
            candidates_df["recency_score"] = 1.0
        else:
            candidates_df["recency_score"] = (candidates_df["date"] - min_date) / (
                max_date - min_date
            )

        candidates_df["final_score"] = candidates_df["event_score"] * (
            1 + recency_weight * candidates_df["recency_score"]
        )
