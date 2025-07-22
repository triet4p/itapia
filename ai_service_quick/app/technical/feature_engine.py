import inspect
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Any, Optional, List, Dict

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Feature Engine')

class _FeatureEngine:
    """Lớp cơ sở trừu tượng cho các Feature Engine.

    Lớp này định nghĩa các hành vi chung và các phương thức cốt lõi mà tất cả
    các feature engine (daily, intraday) phải có. Nó bao gồm việc khởi tạo,
    xử lý NaN, và một phương thức chung để thêm các chỉ báo từ thư viện
    pandas-ta một cách an toàn và linh hoạt.

    Attributes:
        df (pd.DataFrame): DataFrame nội bộ chứa dữ liệu và các đặc trưng đang
            được tính toán.
        DEFAULT_CONFIG (Dict): Một dictionary cấu hình mặc định cho các chỉ báo.
    """
    def __init__(self, ohlcv_df: pd.DataFrame):
        """Khởi tạo Feature Engine với một DataFrame OHLCV."""
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
        """Trả về DataFrame cuối cùng đã được làm giàu với các đặc trưng.

        Hàm này cung cấp các tùy chọn để xử lý giá trị thiếu (NaN) và
        đặt lại index, cho phép người gọi tùy chỉnh output cuối cùng.
        """
        df = self.df.copy() if copy else self.df
        
        if handle_na_method:
            df = self._handle_nans(df, method=handle_na_method)
        
        if reset_index:
            df = df.reset_index(drop=True)
            
        return df
    
    def _handle_nans(self, df: pd.DataFrame, method: str = 'forward_fill') -> pd.DataFrame:
        """
        Xử lý các giá trị NaN trong DataFrame sau khi tính toán các chỉ báo.

        Args:
            df (pd.DataFrame): DataFrame cần xử lý.
            method (str, optional): Phương pháp xử lý.
                'forward_fill': Điền giá trị NaN bằng giá trị hợp lệ gần nhất phía trước.
                'drop_initial': Chỉ xóa các hàng NaN ở đầu DataFrame.
                'mean': Điền bằng giá trị trung bình của cột (ít được khuyến nghị cho chuỗi thời gian).

        Returns:
            pd.DataFrame: DataFrame đã được xử lý NaN.
        """
        logger.info(f"Handling NaNs using '{method}' method...")
        
        if method == 'forward_fill':
            # ffill() sẽ điền các giá trị NaN bằng giá trị hợp lệ cuối cùng.
            # Rất hiệu quả cho các chỉ báo như PSAR khi nó bị "kẹt".
            df.ffill(inplace=True)
        elif method == 'mean':
            df.fillna(df.mean(), inplace=True)

        # Sau khi điền, vẫn có thể còn NaN ở những hàng đầu tiên
        # nếu không có giá trị nào phía trước để điền.
        # Vì vậy, chúng ta vẫn cần drop các hàng NaN còn sót lại này.
        df.dropna(inplace=True)
        
        return df
    
    # --- CORE HELPER FUNCTION (PHIÊN BẢN NÂNG CẤP CUỐI CÙNG) ---
    def _add_generic_indicator(self, indicator_name: str, configs: Optional[List[Dict[str, Any]]] = None):
        """
        Hàm chung để thêm bất kỳ chỉ báo nào từ pandas-ta.
        Chủ động kiểm tra tham số hợp lệ bằng inspect.signature.
        """
        logger.info(f"Adding indicator {indicator_name} to Frame ...")
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

        # Lấy danh sách các tên tham số hợp lệ từ chữ ký của hàm
        valid_params = list(inspect.signature(indicator_function).parameters.keys())
        # Thêm các tham số chung mà pandas-ta sử dụng
        valid_params.extend(['append', 'col_names'])

        for config in configs:
            # Tìm các key không hợp lệ trong config
            invalid_keys = [key for key in config.keys() if key not in valid_params]
            
            if invalid_keys:
                # Nếu có, in cảnh báo và bỏ qua config này
                logger.warn(f"Warning: Invalid parameter(s) {invalid_keys} for '{indicator_name}' with config {config}. "
                     f"Skipping this specific config.")
                continue
            
            # Nếu không có key không hợp lệ, gọi hàm một cách an toàn
            indicator_function(**config, append=True)

        return self

class DailyFeatureEngine(_FeatureEngine):
    """Chuyên gia tạo đặc trưng cho dữ liệu chuỗi thời gian hàng ngày.

    Kế thừa từ _FeatureEngine và định nghĩa một bộ `DEFAULT_CONFIG` riêng,
    tối ưu hóa cho việc phân tích trung và dài hạn. Cung cấp các phương thức
    tiện ích để thêm các nhóm chỉ báo (trend, momentum, etc.) và các
    đặc trưng tùy chỉnh.
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
        logger.info(f"Daily Feature Engine: Adding {group_name} Indicators ---")
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
        logger.info("Daily Feature Engine: Adding Custom: Difference from SMA ...")
        if configs is None: configs = [{'sma_length': 50}, {'sma_length': 200}]
        
        for config in configs:
            sma_length = config.get('sma_length')
            if sma_length:
                sma_col_name = f'SMA_{sma_length}'
                
                # --- LOGIC PHÒNG THỦ Ở ĐÂY ---
                # 1. Kiểm tra xem cột SMA có tồn tại không.
                if sma_col_name not in self.df.columns:
                    print(f"Warning: Column '{sma_col_name}' not found. "
                        f"Possibly not enough data to calculate. Skipping diff calculation for it.")
                    continue # Bỏ qua config này và chuyển sang config tiếp theo

                # 2. Nếu cột tồn tại, tiếp tục tính toán như bình thường.
                new_col_name = f'diff_from_sma_{sma_length}'
                # Thêm 1e-9 để tránh lỗi chia cho 0 nếu SMA bằng 0
                self.df[new_col_name] = (self.df['close'] - self.df[sma_col_name]) / (self.df[sma_col_name] + 1e-9) * 100
                
        return self

    def add_return_d(self, configs: Optional[List[Dict[str, int]]] = None):
        logger.info("Daily Feature Engine: Adding Custom: N-day Return ...")
        if configs is None: configs = [{'d': 1}, {'d': 5}, {'d': 20}]
        for config in configs:
            d_period = config.get('d')
            if d_period:
                self.df[f'return_{d_period}d'] = self.df['close'].pct_change(periods=d_period) * 100
        return self
    
    def add_lag_features(self, configs: Optional[List[Dict[str, any]]] = None):
        logger.info("Daily Feature Engine: Adding Lag Features ...")
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

            # --- Logic phòng thủ: Kiểm tra cột có tồn tại không ---
            if col_to_lag not in self.df.columns:
                logger.warn(f"Error: Column '{col_to_lag}' not found for lagging. "
                    f"Ensure it is calculated before calling add_lag_features. Skipping config {config}.")
                continue

            # Tạo các cột lag
            for period in lag_periods:
                new_col_name = f'{col_to_lag}_lag_{period}'
                self.df[new_col_name] = self.df[col_to_lag].shift(period)

        return self
    
    def add_interaction_features(self):
        """
        Tạo các đặc trưng tương tác có ý nghĩa dựa trên kiến thức chuyên môn,
        kết hợp các tín hiệu từ các nhóm khác nhau (trend, momentum, event).
        """
        logger.info("Daily Feature Engine: Adding Interaction Features ...")
        
        # --- Tương tác 1: Momentum trong bối cảnh Trend ---
        # Yêu cầu: diff_from_sma_200 và RSI_14 phải tồn tại
        if 'diff_from_sma_200' in self.df.columns and 'RSI_14' in self.df.columns:
            self.df['trend_direction'] = np.sign(self.df['diff_from_sma_200'])
            self.df['RSI_x_trend'] = self.df['RSI_14'] * self.df['trend_direction']
            # Có thể xóa cột trung gian nếu muốn
            self.df.drop(columns=['trend_direction'], inplace=True)
            logger.info("  - Added: RSI_x_trend")
        else:
            logger.warn("  - Skipped RSI_x_trend: Required columns not found.")

        # --- Tương tác 2: Momentum được chuẩn hóa bởi Biến động ---
        # Yêu cầu: CCI_14_0.015 và ATRr_14 phải tồn tại
        if 'CCI_14_0.015' in self.df.columns and 'ATRr_14' in self.df.columns:
            # pandas-ta có thể tạo tên cột khác nhau, kiểm tra trước
            cci_col = 'CCI_14_0.015'
            atr_col = 'ATRr_14' # Chú ý 'r' trong ATRr (ATR percentage)
            
            self.df['CCI_norm_by_ATR'] = self.df[cci_col] / (self.df[atr_col] + 1e-9)
            logger.info("  - Added: CCI_norm_by_ATR")
        else:
            logger.warn("  - Skipped CCI_norm_by_ATR: Required columns not found.")
            
        # --- Tương tác 3: Sự kiện Nến trong bối cảnh Trạng thái ---
        # Yêu cầu: CDLHAMMER_3g và RSI_14 phải tồn tại
        if 'CDL_HAMMER' in self.df.columns and 'RSI_14' in self.df.columns:
            self.df['is_oversold'] = (self.df['RSI_14'] < 30).astype(int)
            # Giả sử giá trị của Hammer khi xuất hiện là 100
            self.df['hammer_in_oversold'] = (self.df['CDL_HAMMER'] / 100) * self.df['is_oversold']
            self.df.drop(columns=['is_oversold'], inplace=True)
            logger.info("  - Added: hammer_in_oversold")
        else:
            logger.warn("  - Skipped hammer_in_oversold: Required columns not found.")
            
        return self

    def add_all_candlestick_patterns(self):
        logger.info("Daily Feature Engine: Adding All Candlestick Patterns ...")
        self.df.ta.cdl_pattern(name="all", append=True)
        return self

    def add_all_features(self, all_configs: Optional[Dict[str, List[Dict[str, any]]]] = None):
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
    """Chuyên gia tạo đặc trưng cho dữ liệu chuỗi thời gian trong ngày.

    Kế thừa từ _FeatureEngine và định nghĩa `DEFAULT_CONFIG` phù hợp với các
    khung thời gian ngắn (ví dụ: 15 phút), ưu tiên EMA và các chỉ báo
    nhạy hơn như VWAP. Bao gồm các phương thức đặc thù như `add_opening_range`.
    """
    DEFAULT_CONFIG: Dict[str, List[Dict[str, Any]]] = {
        # Sử dụng EMA làm MA chính
        'ema': [{'length': 9}, {'length': 12}, {'length': 26}],
        # MACD tiêu chuẩn hoạt động rất tốt
        'macd': [{'fast': 12, 'slow': 26, 'signal': 9}],
        # RSI tiêu chuẩn
        'rsi': [{'length': 14}],
        # Bollinger Bands với chu kỳ 26 (tương đương 1 ngày)
        'bbands': [{'length': 26, 'std': 2.0}],
        # ATR để đo biến động của mỗi cây nến 15 phút
        'atr': [{'length': 14}],
        # VWAP không cần tham số, nó sẽ tự reset mỗi ngày
        'vwap': [{}],
    }
    
    def __init__(self, ohlcv_df: pd.DataFrame):
        super().__init__(ohlcv_df)
        
    def add_intraday_ma(self, configs: Optional[List[Dict[str, int]]] = None):
        return self._add_generic_indicator('ema', configs)

    def add_intraday_momentum(self, rsi_configs: Optional[List[Dict]] = None, macd_configs: Optional[List[Dict]] = None):
        self._add_generic_indicator('rsi', rsi_configs)
        self._add_generic_indicator('macd', macd_configs)
        return self

    def add_intraday_volatility(self, bbands_configs: Optional[List[Dict]] = None, atr_configs: Optional[List[Dict]] = None):
        self._add_generic_indicator('bbands', bbands_configs)
        self._add_generic_indicator('atr', atr_configs)
        return self
        
    def add_intraday_volume(self, vwap_configs: Optional[List[Dict]] = None):
        """
        Thêm các chỉ báo khối lượng, đặc biệt là VWAP.
        Lưu ý: pandas-ta sẽ tự động xử lý việc reset VWAP mỗi ngày nếu index là DatetimeIndex.
        """
        # VWAP là quan trọng nhất
        self._add_generic_indicator('vwap', vwap_configs)
        # Có thể thêm MFI nếu muốn
        # self._add_generic_indicator('mfi', [{'length': 14}])
        return self

    def add_opening_range(self, minutes: int = 30):
        logger.info(f"Intraday Feature Engine: Adding {minutes}-minute Opening Range...")
        
        # Lấy ngày của mỗi dòng để nhóm
        df_date = self.df.index.date
        
        # Hàm helper để tính OR
        def get_or(x, minutes):
            # Xác định thời gian bắt đầu và kết thúc của Opening Range
            # between_time bao gồm cả start và end, nên cần cẩn thận
            # Ví dụ: 9:30 -> 9:59 (cho 30 phút)
            start_time = x.index[0].time()
            # Tính toán end_time một cách an toàn hơn
            end_time = (pd.to_datetime(f"1970-01-01 {start_time}") + pd.Timedelta(minutes=minutes-1)).time()
            
            opening_range_df = x.between_time(start_time, end_time, inclusive='both')
            
            if opening_range_df.empty:
                return np.nan, np.nan
                
            return opening_range_df['high'].max(), opening_range_df['low'].min()
            
        # Nhóm theo ngày và tính OR
        or_levels = self.df.groupby(df_date).apply(lambda x: get_or(x, minutes))
        
        # or_levels là một Series với index là các ngày và value là các tuple (high, low)
        # Tách Series này thành 2 Series riêng biệt cho high và low
        or_high_series = or_levels.str[0]
        or_low_series = or_levels.str[1]
        
        # Tạo các cột mới trong DataFrame gốc bằng cách map Series or_high/low
        # vào df gốc dựa trên ngày của index
        # self.df.index.to_series().dt.date sẽ tạo ra một Series các ngày
        self.df[f'OR_{minutes}m_High'] = self.df.index.to_series().dt.date.map(or_high_series)
        self.df[f'OR_{minutes}m_Low'] = self.df.index.to_series().dt.date.map(or_low_series)
        
        return self

    def add_all_intraday_features(self):
        """Hàm tiện ích để thêm tất cả các chỉ báo intraday tiêu chuẩn."""
        logger.info("Intraday Feature Engine: Adding all standard intraday features ...")
        (self
            .add_intraday_ma()
            .add_intraday_momentum()
            .add_intraday_volatility()
            .add_intraday_volume()
            .add_opening_range(minutes=30) # Thêm vùng giá 30 phút đầu ngày
        )
        return self
