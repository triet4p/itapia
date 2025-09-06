"""Feature engineering engines for technical analysis of financial time series data."""

import inspect
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Any, Optional, List, Dict

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Feature Engine')


class _FeatureEngine:
    """Abstract base class for Feature Engines.
    
    This class defines common behaviors and core methods that all feature engines 
    (daily, intraday) must have. It includes initialization, NaN handling, and a 
    common method to safely and flexibly add indicators from the pandas-ta library.
    
    Attributes:
        df (pd.DataFrame): Internal DataFrame containing data and features being computed.
        DEFAULT_CONFIG (Dict): A dictionary of default configurations for indicators.
    """
    
    def __init__(self, ohlcv_df: pd.DataFrame):
        """Initialize Feature Engine with an OHLCV DataFrame.
        
        Args:
            ohlcv_df (pd.DataFrame): DataFrame with Open, High, Low, Close, Volume data
            
        Raises:
            TypeError: If DataFrame index is not a DatetimeIndex
            ValueError: If required columns are missing from the DataFrame
        """
        if not isinstance(ohlcv_df.index, pd.DatetimeIndex):
            raise TypeError("DataFrame index must be a DatetimeIndex for intraday analysis.")
        
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        self.df = ohlcv_df.copy()
        self.df.columns = [col.lower() for col in self.df.columns]
        if not all(col in self.df.columns for col in required_cols):
            raise ValueError(f"DataFrame must have cols: {required_cols}")
        if 'ta' in self.df.columns:
            self.df.drop(columns=['ta'], inplace=True)
            
    def get_features(self, copy: bool = True, handle_na_method: Optional[str] = 'forward_fill', reset_index: bool = False) -> pd.DataFrame:
        """Return the final DataFrame enriched with features.
        
        This function provides options to handle missing values (NaN) and 
        reset the index, allowing the caller to customize the final output.
        
        Args:
            copy (bool, optional): Whether to return a copy of the DataFrame. Defaults to True.
            handle_na_method (Optional[str], optional): Method to handle NaN values. Defaults to 'forward_fill'.
            reset_index (bool, optional): Whether to reset the DataFrame index. Defaults to False.
            
        Returns:
            pd.DataFrame: Feature-enriched DataFrame
        """
        df = self.df.copy() if copy else self.df
        
        if handle_na_method:
            df = self._handle_nans(df, method=handle_na_method)
        
        if reset_index:
            df = df.reset_index(drop=True)
            
        return df
    
    def _handle_nans(self, df: pd.DataFrame, method: str = 'forward_fill') -> pd.DataFrame:
        """Handle NaN values in DataFrame after computing indicators.
        
        Args:
            df (pd.DataFrame): DataFrame to process
            method (str, optional): Processing method.
                'forward_fill': Fill NaN values with the nearest valid preceding value.
                'drop_initial': Only drop NaN rows at the beginning of the DataFrame.
                'mean': Fill with column mean (not recommended for time series).
                
        Returns:
            pd.DataFrame: DataFrame with processed NaN values
        """
        logger.info(f"Handling NaNs using '{method}' method...")
        
        if method == 'forward_fill':
            # ffill() will fill NaN values with the last valid value.
            # Very effective for indicators like PSAR when it gets "stuck".
            df.ffill(inplace=True)
        elif method == 'mean':
            df.fillna(df.mean(), inplace=True)

        # After filling, there may still be NaN in the first rows
        # if there's no preceding value to fill with.
        # So we still need to drop remaining NaN rows.
        df.dropna(inplace=True)
        
        return df
    
    # --- CORE HELPER FUNCTION (FINAL ENHANCED VERSION) ---
    def _add_generic_indicator(self, indicator_name: str, configs: Optional[List[Dict[str, Any]]] = None):
        """Generic function to add any indicator from pandas-ta.
        
        Actively validates parameters using inspect.signature.
        
        Args:
            indicator_name (str): Name of the indicator to add
            configs (Optional[List[Dict[str, Any]]], optional): Configuration parameters. 
                If None, uses DEFAULT_CONFIG.
                
        Returns:
            Self: Returns self for method chaining
        """
        logger.debug(f"Adding indicator {indicator_name} to Frame ...")
        if configs is None:
            configs = self.DEFAULT_CONFIG.get(indicator_name)
            if configs is None:
                logger.warn(f"Warning: No default config for '{indicator_name}'. Skipping.")
                return self
        try:
            indicator_function = getattr(self.df.ta, indicator_name)
        except AttributeError:
            logger.err(f"Warning: Indicator '{indicator_name}' not found in pandas-ta. Skipping.")
            return self

        # Get list of valid parameter names from function signature
        valid_params = list(inspect.signature(indicator_function).parameters.keys())
        # Add common parameters that pandas-ta uses
        valid_params.extend(['append', 'col_names'])

        for config in configs:
            # Find invalid keys in config
            invalid_keys = [key for key in config.keys() if key not in valid_params]
            
            if invalid_keys:
                # If there are any, warn and skip this config
                logger.warn(f"Warning: Invalid parameter(s) {invalid_keys} for '{indicator_name}' with config {config}. "
                     f"Skipping this specific config.")
                continue
            
            # If no invalid keys, call function safely
            indicator_function(**config, append=True)

        return self


class DailyFeatureEngine(_FeatureEngine):
    """Feature generator expert for daily time series data.
    
    Inherits from _FeatureEngine and defines its own `DEFAULT_CONFIG`,
    optimized for medium and long-term analysis. Provides utility methods
    to add indicator groups (trend, momentum, etc.) and custom features.
    """
    
    DEFAULT_CONFIG: Dict[str, List[Dict[str, any]]] = {
        # Trend indicators
        'sma': [{'length': 20}, {'length': 50}, {'length': 200}],
        'ema': [{'length': 20}, {'length': 50}, {'length': 200}],
        'macd': [{'fast': 12, 'slow': 26, 'signal': 9}],
        'adx': [{'length': 14}],
        'psar': [{}],
        # Momentum indicators
        'rsi': [{'length': 14}],
        'stoch': [{}],
        'cci': [{'length': 14}],
        'willr': [{'length': 14}],
        # Volatility indicators
        'bbands': [{'length': 20, 'std': 2.0}],
        'atr': [{'length': 14}],
        'donchian': [{'lower_length': 20, 'upper_length': 20}],
        # Volume indicators
        'mfi': [{'length': 14}],
        'obv': [{}],
        'vwap': [{}],
        # Custom
        'diff_from_sma': [{'sma_length': 50}, {'sma_length': 200}],
        'return_d': [{'d': 1}, {'d': 5}, {'d': 20}],
        'lag': [
            {'column': 'close', 'periods': [1, 3, 5, 10, 20, 40]},
            {'column': 'volume', 'periods': [1, 3, 5, 10, 20, 40]},
            {'column': 'return_1d', 'periods': [1, 5, 20]},
            {'column': 'diff_from_sma_50', 'periods': [1, 5, 20, 40]}
        ]
    }
    
    def __init__(self, ohlcv_df: pd.DataFrame):
        """Initialize DailyFeatureEngine with OHLCV DataFrame.
        
        Args:
            ohlcv_df (pd.DataFrame): DataFrame with Open, High, Low, Close, Volume data
        """
        super().__init__(ohlcv_df)

    # --- INDICATOR WRAPPER METHODS ---
    def add_sma(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('sma', configs)

    def add_ema(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('ema', configs)

    def add_macd(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('macd', configs)

    def add_adx(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('adx', configs)

    def add_psar(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('psar', configs)

    def add_rsi(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('rsi', configs)

    def add_stoch(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('stoch', configs)

    def add_cci(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('cci', configs)

    def add_willr(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('willr', configs)

    def add_bbands(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('bbands', configs)

    def add_atr(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('atr', configs)

    def add_donchian(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('donchian', configs)

    def add_mfi(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('mfi', configs)

    def add_obv(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('obv', configs)

    def add_vwap(self, configs: Optional[List[Dict[str, any]]] = None):
        return self._add_generic_indicator('vwap', configs)

    # --- GROUP METHODS ---
    def _add_indicator_group(self, group_name: str, indicators: List[str], all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        """Add a group of indicators.
        
        Args:
            group_name (str): Name of the indicator group
            indicators (List[str]): List of indicator names to add
            all_configs (Optional[Dict[str, List[Dict[str, any]]]], optional): Configurations for all indicators
            
        Returns:
            Self: Returns self for method chaining
        """
        logger.debug(f"Daily Feature Engine: Adding {group_name} Indicators ---")
        for indicator in indicators:
            indicator_config = all_configs.get(indicator) if all_configs else None
            getattr(self, f'add_{indicator}')(indicator_config)
        return self

    def add_trend_indicators(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        """Add trend-related indicators.
        
        Args:
            all_configs (Optional[Dict[str, List[Dict[str, any]]]], optional): Configurations for all indicators
            
        Returns:
            Self: Returns self for method chaining
        """
        return self._add_indicator_group('Trend', ['sma', 'ema', 'macd', 'adx', 'psar'], all_configs)

    def add_momentum_indicators(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        """Add momentum-related indicators.
        
        Args:
            all_configs (Optional[Dict[str, List[Dict[str, any]]]], optional): Configurations for all indicators
            
        Returns:
            Self: Returns self for method chaining
        """
        return self._add_indicator_group('Momentum', ['rsi', 'stoch', 'cci', 'willr'], all_configs)

    def add_volatility_indicators(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        """Add volatility-related indicators.
        
        Args:
            all_configs (Optional[Dict[str, List[Dict[str, any]]]], optional): Configurations for all indicators
            
        Returns:
            Self: Returns self for method chaining
        """
        return self._add_indicator_group('Volatility', ['bbands', 'atr', 'donchian'], all_configs)

    def add_volume_indicators(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        """Add volume-related indicators.
        
        Args:
            all_configs (Optional[Dict[str, List[Dict[str, any]]]], optional): Configurations for all indicators
            
        Returns:
            Self: Returns self for method chaining
        """
        return self._add_indicator_group('Volume', ['mfi', 'obv', 'vwap'], all_configs)

    # --- CUSTOM & AGGREGATE METHODS ---
    def add_diff_from_sma(self, configs: Optional[List[Dict[str, int]]] = None):
        """Add custom feature: Difference from SMA.
        
        Args:
            configs (Optional[List[Dict[str, int]]], optional): SMA length configurations
            
        Returns:
            Self: Returns self for method chaining
        """
        logger.debug("Daily Feature Engine: Adding Custom: Difference from SMA ...")
        if configs is None: configs = [{'sma_length': 50}, {'sma_length': 200}]
        
        for config in configs:
            sma_length = config.get('sma_length')
            if sma_length:
                sma_col_name = f'SMA_{sma_length}'
                
                # --- DEFENSIVE LOGIC HERE ---
                # 1. Check if SMA column exists
                if sma_col_name not in self.df.columns:
                    logger.warn(f"Warning: Column '{sma_col_name}' not found. "
                        f"Possibly not enough data to calculate. Skipping diff calculation for it.")
                    continue  # Skip this config and move to the next one

                # 2. If column exists, continue calculation as normal
                new_col_name = f'diff_from_sma_{sma_length}'
                # Add 1e-9 to avoid division by zero if SMA is 0
                self.df[new_col_name] = (self.df['close'] - self.df[sma_col_name]) / (self.df[sma_col_name] + 1e-9) * 100
                
        return self

    def add_return_d(self, configs: Optional[List[Dict[str, int]]] = None):
        """Add custom feature: N-day Return.
        
        Args:
            configs (Optional[List[Dict[str, int]]], optional): Return period configurations
            
        Returns:
            Self: Returns self for method chaining
        """
        logger.debug("Daily Feature Engine: Adding Custom: N-day Return ...")
        if configs is None: configs = [{'d': 1}, {'d': 5}, {'d': 20}]
        for config in configs:
            d_period = config.get('d')
            if d_period:
                self.df[f'return_{d_period}d'] = self.df['close'].pct_change(periods=d_period) * 100
        return self
    
    def add_lag_features(self, configs: Optional[List[Dict[str, any]]] = None):
        """Add lag features.
        
        Args:
            configs (Optional[List[Dict[str, any]]], optional): Lag configurations
            
        Returns:
            Self: Returns self for method chaining
        """
        logger.debug("Daily Feature Engine: Adding Lag Features ...")
        if configs is None:
            configs = self.DEFAULT_CONFIG.get('lag')

        if not configs:
            logger.warn("Warning: No config found for 'lag'. Skipping.")
            return self

        for config in configs:
            col_to_lag = config.get('column')
            lag_periods = config.get('periods')

            if not col_to_lag or not lag_periods:
                logger.warn(f"Warning: Invalid lag config {config}. Missing 'column' or 'periods'. Skipping.")
                continue

            # --- Defensive logic: Check if column exists ---
            if col_to_lag not in self.df.columns:
                logger.warn(f"Error: Column '{col_to_lag}' not found for lagging. "
                    f"Ensure it is calculated before calling add_lag_features. Skipping config {config}.")
                continue

            # Create lag columns
            for period in lag_periods:
                new_col_name = f'{col_to_lag}_lag_{period}'
                self.df[new_col_name] = self.df[col_to_lag].shift(period)

        return self
    
    def add_interaction_features(self):
        """Create meaningful interaction features based on domain knowledge,
        combining signals from different groups (trend, momentum, event).
        
        Returns:
            Self: Returns self for method chaining
        """
        logger.debug("Daily Feature Engine: Adding Interaction Features ...")
        
        # --- Interaction 1: Momentum in Trend Context ---
        # Requirement: diff_from_sma_200 and RSI_14 must exist
        if 'diff_from_sma_200' in self.df.columns and 'RSI_14' in self.df.columns:
            self.df['trend_direction'] = np.sign(self.df['diff_from_sma_200'])
            self.df['RSI_x_trend'] = self.df['RSI_14'] * self.df['trend_direction']
            # Can delete intermediate column if desired
            self.df.drop(columns=['trend_direction'], inplace=True)
            logger.debug("  - Added: RSI_x_trend")
        else:
            logger.warn("  - Skipped RSI_x_trend: Required columns not found.")

        # --- Interaction 2: Momentum Normalized by Volatility ---
        # Requirement: CCI_14_0.015 and ATRr_14 must exist
        if 'CCI_14_0.015' in self.df.columns and 'ATRr_14' in self.df.columns:
            # pandas-ta may create different column names, check first
            cci_col = 'CCI_14_0.015'
            atr_col = 'ATRr_14'  # Note 'r' in ATRr (ATR percentage)
            
            self.df['CCI_norm_by_ATR'] = self.df[cci_col] / (self.df[atr_col] + 1e-9)
            logger.debug("  - Added: CCI_norm_by_ATR")
        else:
            logger.warn("  - Skipped CCI_norm_by_ATR: Required columns not found.")
            
        # --- Interaction 3: Candle Events in State Context ---
        # Requirement: CDLHAMMER_3g and RSI_14 must exist
        if 'CDL_HAMMER' in self.df.columns and 'RSI_14' in self.df.columns:
            self.df['is_oversold'] = (self.df['RSI_14'] < 30).astype(int)
            # Assume Hammer value when appearing is 100
            self.df['hammer_in_oversold'] = (self.df['CDL_HAMMER'] / 100) * self.df['is_oversold']
            self.df.drop(columns=['is_oversold'], inplace=True)
            logger.debug("  - Added: hammer_in_oversold")
        else:
            logger.warn("  - Skipped hammer_in_oversold: Required columns not found.")
            
        return self

    def add_all_candlestick_patterns(self):
        """Add all candlestick pattern indicators.
        
        Returns:
            Self: Returns self for method chaining
        """
        logger.debug("Daily Feature Engine: Adding All Candlestick Patterns ...")
        self.df.ta.cdl_pattern(name="all", append=True)
        return self

    def add_all_features(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        """Utility function to add all standard features.
        
        Args:
            all_configs (Optional[Dict[str, List[Dict[str, any]]]], optional): Configurations for all indicators
            
        Returns:
            Self: Returns self for method chaining
        """
        logger.info("Daily Feature Engine: === Adding All Features ===")
        (self.add_trend_indicators(all_configs)
             .add_momentum_indicators(all_configs)
             .add_volatility_indicators(all_configs)
             .add_volume_indicators(all_configs)
             .add_diff_from_sma(all_configs.get('diff_from_sma') if all_configs else None)
             .add_return_d(all_configs.get('return_d') if all_configs else None)
             .add_lag_features(all_configs.get('lag') if all_configs else None)
             .add_all_candlestick_patterns()
             .add_interaction_features())
        return self
    

class IntradayFeatureEngine(_FeatureEngine):
    """Feature generator expert for intraday time series data.
    
    Inherits from _FeatureEngine and defines `DEFAULT_CONFIG` appropriate for 
    short time frames (e.g., 15 minutes), prioritizing EMA and more sensitive 
    indicators like VWAP. Includes specific methods like `add_opening_range`.
    """
    
    DEFAULT_CONFIG: Dict[str, List[Dict[str, Any]]] = {
        # Use EMA as main MA
        'ema': [{'length': 9}, {'length': 12}, {'length': 26}],
        # Standard MACD works very well
        'macd': [{'fast': 12, 'slow': 26, 'signal': 9}],
        # Standard RSI
        'rsi': [{'length': 14}],
        # Bollinger Bands with 26 period (equivalent to 1 day)
        'bbands': [{'length': 26, 'std': 2.0}],
        # ATR to measure volatility of each 15-minute candle
        'atr': [{'length': 14}],
        # VWAP needs no parameters, it will reset daily
        'vwap': [{}],
    }
    
    def __init__(self, ohlcv_df: pd.DataFrame):
        """Initialize IntradayFeatureEngine with OHLCV DataFrame.
        
        Args:
            ohlcv_df (pd.DataFrame): DataFrame with Open, High, Low, Close, Volume data
        """
        super().__init__(ohlcv_df)
        
    def add_intraday_ma(self, configs: Optional[List[Dict[str, int]]] = None):
        """Add intraday moving average indicators.
        
        Args:
            configs (Optional[List[Dict[str, int]]], optional): MA configurations
            
        Returns:
            Self: Returns self for method chaining
        """
        return self._add_generic_indicator('ema', configs)

    def add_intraday_momentum(self, rsi_configs: Optional[List[Dict]] = None, macd_configs: Optional[List[Dict]] = None):
        """Add intraday momentum indicators.
        
        Args:
            rsi_configs (Optional[List[Dict]], optional): RSI configurations
            macd_configs (Optional[List[Dict]], optional): MACD configurations
            
        Returns:
            Self: Returns self for method chaining
        """
        self._add_generic_indicator('rsi', rsi_configs)
        self._add_generic_indicator('macd', macd_configs)
        return self

    def add_intraday_volatility(self, bbands_configs: Optional[List[Dict]] = None, atr_configs: Optional[List[Dict]] = None):
        """Add intraday volatility indicators.
        
        Args:
            bbands_configs (Optional[List[Dict]], optional): Bollinger Bands configurations
            atr_configs (Optional[List[Dict]], optional): ATR configurations
            
        Returns:
            Self: Returns self for method chaining
        """
        self._add_generic_indicator('bbands', bbands_configs)
        self._add_generic_indicator('atr', atr_configs)
        return self
        
    def add_intraday_volume(self, vwap_configs: Optional[List[Dict]] = None):
        """Add volume indicators, especially VWAP.
        
        Note: pandas-ta will automatically handle VWAP reset daily if index is DatetimeIndex.
        
        Args:
            vwap_configs (Optional[List[Dict]], optional): VWAP configurations
            
        Returns:
            Self: Returns self for method chaining
        """
        # VWAP is most important
        self._add_generic_indicator('vwap', vwap_configs)
        # Can add MFI if desired
        # self._add_generic_indicator('mfi', [{'length': 14}])
        return self

    def add_opening_range(self, minutes: int = 30):
        """Add opening range feature.
        
        Args:
            minutes (int, optional): Minutes for opening range calculation. Defaults to 30.
            
        Returns:
            Self: Returns self for method chaining
        """
        logger.debug(f"Intraday Feature Engine: Adding {minutes}-minute Opening Range...")
        
        # Get date of each row for grouping
        df_date = self.df.index.date
        
        # Helper function to calculate OR
        def get_or(x, minutes):
            # Determine start and end time of Opening Range
            # between_time includes both start and end, so need to be careful
            # Example: 9:30 -> 9:59 (for 30 minutes)
            start_time = x.index[0].time()
            # Calculate end_time more safely
            end_time = (pd.to_datetime(f"1970-01-01 {start_time}") + pd.Timedelta(minutes=minutes-1)).time()
            
            opening_range_df = x.between_time(start_time, end_time, inclusive='both')
            
            if opening_range_df.empty:
                return np.nan, np.nan
                
            return opening_range_df['high'].max(), opening_range_df['low'].min()
            
        # Group by date and calculate OR
        or_levels = self.df.groupby(df_date).apply(lambda x: get_or(x, minutes))
        
        # or_levels is a Series with index as dates and value as tuples (high, low)
        # Split this Series into 2 separate Series for high and low
        or_high_series = or_levels.str[0]
        or_low_series = or_levels.str[1]
        
        # Create new columns in original DataFrame by mapping or_high/low Series
        # into the original df based on index date
        # self.df.index.to_series().dt.date will create a Series of dates
        self.df[f'OR_{minutes}m_High'] = self.df.index.to_series().dt.date.map(or_high_series)
        self.df[f'OR_{minutes}m_Low'] = self.df.index.to_series().dt.date.map(or_low_series)
        
        return self

    def add_all_intraday_features(self):
        """Utility function to add all standard intraday indicators.
        
        Returns:
            Self: Returns self for method chaining
        """
        logger.info("Intraday Feature Engine: Adding all standard intraday features ...")
        (self
            .add_intraday_ma()
            .add_intraday_momentum()
            .add_intraday_volatility()
            .add_intraday_volume()
            .add_opening_range(minutes=30)  # Add 30-minute opening range
        )
        return self