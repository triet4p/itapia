import inspect
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Any, Optional, List, Dict

class FeatureEngine:
    DEFAULT_CONFIG: Dict[str, List[Dict[str, any]]] = {
        # Trend indicators
        'sma': [{'length': 20}, {'length': 50}, {'length': 200}],
        'ema': [{'length': 20}, {'length': 50}, {'length': 200}],
        'macd': [{'fast': 12, 'slow': 26, 'signal': 9}],
        'adx': [{'length': 14}],
        'psar': [{'initial': 0.02, 'acceleration': 0.02, 'maximum': 0.2}],
        # Momentum indicators
        'rsi': [{'length': 14}],
        'stoch': [{'k': 14, 'd': 3, 'smooth_k': 3}],
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
        'return_d': [{'d': 5}, {'d': 20}] 
    }
    
    def __init__(self, ohlcv_df: pd.DataFrame):
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        self.df = ohlcv_df.copy()
        self.df.columns = [col.lower() for col in self.df.columns]
        if not all(col in self.df.columns for col in required_cols):
            raise ValueError(f"DataFrame must have cols: {required_cols}")
        if 'ta' in self.df.columns:
            self.df.drop(columns=['ta'], inplace=True)
        
    def get_features(self, copy: bool = True, dropna: bool = True, reset_index: bool = True) -> pd.DataFrame:
        df = self.df.copy() if copy else self.df
        
        if dropna:
            df = df.dropna()
        
        if reset_index:
            df = df.reset_index(drop=True)
            
        return df
    
    # --- CORE HELPER FUNCTION (PHIÊN BẢN NÂNG CẤP CUỐI CÙNG) ---
    def _add_generic_indicator(self, indicator_name: str, configs: Optional[List[Dict[str, Any]]] = None):
        """
        Hàm chung để thêm bất kỳ chỉ báo nào từ pandas-ta.
        Chủ động kiểm tra tham số hợp lệ bằng inspect.signature.
        """
        if configs is None:
            configs = self.DEFAULT_CONFIG.get(indicator_name)
            if configs is None:
                print(f"Warning: No default config for '{indicator_name}'. Skipping.")
                return self
        try:
            indicator_function = getattr(self.df.ta, indicator_name)
        except AttributeError:
            print(f"Warning: Indicator '{indicator_name}' not found in pandas-ta. Skipping.")
            return self

        # Lấy danh sách các tên tham số hợp lệ từ chữ ký của hàm
        valid_params = list(inspect.signature(indicator_function).parameters.keys())
        # Thêm các tham số chung mà pandas-ta sử dụng
        valid_params.extend(['append', 'col_names'])

        for config in configs:
            # Tìm các key không hợp lệ trong config
            invalid_keys = [key for key in config.keys() if key not in valid_params]
            
            if invalid_keys:
                # Nếu có, in cảnh báo và bỏ qua config này
                print(f"Warning: Invalid parameter(s) {invalid_keys} for '{indicator_name}' with config {config}. "
                      f"Skipping this specific config.")
                continue
            
            # Nếu không có key không hợp lệ, gọi hàm một cách an toàn
            indicator_function(**config, append=True)

        return self

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
        print(f"--- Adding {group_name} Indicators ---")
        for indicator in indicators:
            indicator_config = all_configs.get(indicator) if all_configs else None
            getattr(self, f'add_{indicator}')(indicator_config)
        return self

    def add_trend_indicators(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        return self._add_indicator_group('Trend', ['sma', 'ema', 'macd', 'adx', 'psar'], all_configs)

    def add_momentum_indicators(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        return self._add_indicator_group('Momentum', ['rsi', 'stoch', 'cci', 'willr'], all_configs)

    def add_volatility_indicators(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        return self._add_indicator_group('Volatility', ['bbands', 'atr', 'donchian'], all_configs)

    def add_volume_indicators(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        return self._add_indicator_group('Volume', ['mfi', 'obv', 'vwap'], all_configs)

    # --- CUSTOM & AGGREGATE METHODS ---
    def add_diff_from_sma(self, configs: Optional[List[Dict[str, int]]] = None):
        print("--- Adding Custom: Difference from SMA ---")
        if configs is None: configs = [{'sma_length': 50}, {'sma_length': 200}]
        for config in configs:
            sma_length = config.get('sma_length')
            if sma_length:
                sma_col_name = f'SMA_{sma_length}'
                if sma_col_name not in self.df.columns:
                    print(f"Info: '{sma_col_name}' not found. Calculating it for diff calculation.")
                    self.add_sma(configs=[{'length': sma_length}])
                
                new_col_name = f'diff_from_sma_{sma_length}'
                # Thêm 1e-9 để tránh lỗi chia cho 0 nếu SMA bằng 0
                self.df[new_col_name] = (self.df['close'] - self.df[sma_col_name]) / (self.df[sma_col_name] + 1e-9) * 100
        return self

    def add_return_d(self, configs: Optional[List[Dict[str, int]]] = None):
        print("--- Adding Custom: N-day Return ---")
        if configs is None: configs = [{'d': 1}, {'d': 5}, {'d': 20}]
        for config in configs:
            d_period = config.get('d')
            if d_period:
                self.df[f'return_{d_period}d'] = self.df['close'].pct_change(periods=d_period) * 100
        return self

    def add_all_candlestick_patterns(self):
        print("--- Adding All Candlestick Patterns ---")
        self.df.ta.cdl_pattern(name="all", append=True)
        return self

    def add_all_features(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
        print("=== Adding All Features ===")
        (self.add_trend_indicators(all_configs)
             .add_momentum_indicators(all_configs)
             .add_volatility_indicators(all_configs)
             .add_volume_indicators(all_configs)
             .add_diff_from_sma(all_configs.get('diff_from_sma') if all_configs else None)
             .add_return_d(all_configs.get('return_d') if all_configs else None)
             .add_all_candlestick_patterns())
        return self

    def get_features(self, copy: bool = True, dropna: bool = True, reset_index: bool = True) -> pd.DataFrame:
        df = self.df.copy() if copy else self.df
        if dropna:
            df = df.dropna()
        if reset_index:
            df = df.reset_index(drop=True)
        return df