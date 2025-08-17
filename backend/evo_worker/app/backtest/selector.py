import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Set

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Backtest Point Selector')

class BacktestPointSelector:
    DEFAULT_CONFIG = {
        'volatility_quantile': 0.95,
        'recency_weight': 0.5,
    }
    """
    Một class thông minh để lựa chọn các ngày "đặc biệt" đáng để backtest từ
    dữ liệu lịch sử OHLCV, sử dụng các hàm tính toán của Pandas, không phụ thuộc TA-Lib.
    
    Hỗ trợ chaining methods để xây dựng một tập hợp các điểm backtest.
    """
    def __init__(self, ohlcv_df: pd.DataFrame, 
                 selector_start: datetime|None = None,
                 selector_end: datetime|None = None,
                 config: Dict = None):
        """
        Khởi tạo selector với DataFrame OHLCV.
        
        Args:
            ohlcv_df (pd.DataFrame): DataFrame chứa dữ liệu giá lịch sử,
                                     phải có DatetimeIndex và các cột 'open', 'high', 'low', 'close'.
            config (Dict, optional): Một dictionary để tinh chỉnh các tham số.
        """
        if ohlcv_df.empty:
            raise ValueError("OHLCV DataFrame cannot be empty.")
        
        self.config = config or self.DEFAULT_CONFIG
        
        self.df = ohlcv_df.copy()
        self.selector_start = selector_start.replace(tzinfo=timezone.utc) if selector_start else self.df.index.min().to_pydatetime()
        self.selector_end = selector_end.replace(tzinfo=timezone.utc) if selector_end else self.df.index.max().to_pydatetime()
    
        # 1. Chuẩn bị dữ liệu và các chỉ báo MỘT LẦN DUY NHẤT
        self._calculate_indicators()
        
        # 2. Sử dụng một Set để lưu trữ các điểm được chọn, tự động xử lý trùng lặp
        self.selected_points: Set[pd.Timestamp] = set()

    def _calculate_indicators(self):
        """Tính toán tất cả các chỉ báo cần thiết để phát hiện sự kiện bằng Pandas."""
        logger.info("Calculating base indicators for point selection using Pandas...")
        
        # Tính RSI bằng Pandas
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.df['rsi'] = 100 - (100 / (1 + rs))

        # Tính SMA bằng Pandas
        self.df['sma_50'] = self.df['close'].rolling(window=50).mean()
        self.df['sma_200'] = self.df['close'].rolling(window=200).mean()

        # Tính % thay đổi giá hàng ngày
        self.df['daily_change_pct'] = self.df['close'].pct_change().abs() * 100
        
        # Bỏ qua các hàng NaN được tạo ra bởi các chỉ báo (chủ yếu là do SMA_200)
        self.df.dropna(inplace=True)

    def add_monthly_points(self, day_of_month: int) -> 'BacktestPointSelector':
        """
        Thêm các điểm backtest định kỳ hàng tháng.
        """
        logger.info(f"Adding monthly points on day {day_of_month}...")
        
        
        monthly_dates: List[pd.Timestamp] = []
        for month_start_date in pd.date_range(start=self.selector_start, end=self.selector_end, freq='MS'):
            target_date = month_start_date.replace(day=day_of_month)
            monthly_dates.append(target_date)
        monthly_dates_idx = pd.to_datetime(monthly_dates, utc=True)
        
        for monthly_idx in monthly_dates_idx:
            curr_df = self.df[self.df.index <= monthly_idx]
            self.selected_points.add(curr_df.iloc[-1].name)
        
        return self

    def add_significant_points(self, max_points: int = 100) -> 'BacktestPointSelector':
        """
        Thêm các điểm backtest "đặc biệt" dựa trên các sự kiện kỹ thuật.
        """
        logger.info(f"Adding up to {max_points} significant points...")
        volatility_points = self._find_volatility_spikes()
        trend_change_points = self._find_trend_changes()
        momentum_points = self._find_momentum_extremes()

        all_candidates = pd.concat([volatility_points, trend_change_points, momentum_points])
        if all_candidates.empty:
            logger.warn("No significant points found.")
            return self
            
        all_candidates.sort_values(by='event_score', ascending=False, inplace=True)
        distinct_candidates = all_candidates.drop_duplicates(subset=['date'], keep='first').copy()

        self._apply_recency_bias(distinct_candidates)
        
        top_points = distinct_candidates.sort_values(by='final_score', ascending=False).head(max_points)
        
        for point in top_points['date']:
            if point.to_pydatetime() > self.selector_end:
                continue
            if point.to_pydatetime() < self.selector_start:
                continue
            self.selected_points.add(point)
            
        return self

    def get_points(self) -> List[datetime]:
        """
        Trả về danh sách cuối cùng của các điểm backtest đã được chọn, đã sắp xếp.
        """
        if not self.selected_points:
            return []
        return sorted([ts.to_pydatetime() for ts in self.selected_points])

    def get_points_as_timestamps(self) -> List[int]:
        """
        Trả về danh sách cuối cùng của các điểm backtest dưới dạng Unix timestamps (integer), đã sắp xếp.
        Rất hữu ích để gửi qua API.
        
        Returns:
            List[int]: Danh sách các Unix timestamps.
        """
        if not self.selected_points:
            return []
        # Chuyển đổi thành integer timestamp và sắp xếp
        return sorted([int(ts.timestamp()) for ts in self.selected_points])
    
    # --- CÁC HÀM HỖ TRỢ (PRIVATE) ---
    def _find_volatility_spikes(self) -> pd.DataFrame:
        quantile = self.config.get('volatility_quantile', 0.95)
        spike_threshold = self.df['daily_change_pct'].quantile(quantile)
        spikes = self.df[self.df['daily_change_pct'] >= spike_threshold]
        return pd.DataFrame({'date': spikes.index, 'event_score': 0.7})

    def _find_trend_changes(self) -> pd.DataFrame:
        df = self.df
        golden_cross = (df['sma_50'] > df['sma_200']) & (df['sma_50'].shift(1) <= df['sma_200'].shift(1))
        death_cross = (df['sma_50'] < df['sma_200']) & (df['sma_50'].shift(1) >= df['sma_200'].shift(1))
        crosses = df[golden_cross | death_cross]
        return pd.DataFrame({'date': crosses.index, 'event_score': 1.0})

    def _find_momentum_extremes(self) -> pd.DataFrame:
        df = self.df
        overbought = (df['rsi'] > 70) & (df['rsi'].shift(1) <= 70)
        oversold = (df['rsi'] < 30) & (df['rsi'].shift(1) >= 30)
        extremes = df[overbought | oversold]
        return pd.DataFrame({'date': extremes.index, 'event_score': 0.8})

    def _apply_recency_bias(self, candidates_df: pd.DataFrame):
        recency_weight = self.config.get('recency_weight', 0.5)
        min_date = candidates_df['date'].min()
        max_date = candidates_df['date'].max()
        
        if max_date == min_date:
            candidates_df['recency_score'] = 1.0
        else:
            candidates_df['recency_score'] = (candidates_df['date'] - min_date) / (max_date - min_date)
            
        candidates_df['final_score'] = candidates_df['event_score'] * (1 + recency_weight * candidates_df['recency_score'])