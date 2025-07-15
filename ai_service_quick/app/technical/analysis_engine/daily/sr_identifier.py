import pandas as pd
from typing import Dict, Any, List, Tuple
import numpy as np

class DailySRIdentifier:
    """
    Chuyên gia xác định các mức Hỗ trợ (Support) và Kháng cự (Resistance).
    Phiên bản 1 (v1) tập trung vào các phương pháp không phụ thuộc vào PatternRecognizer.
    """
    def __init__(self, feature_df: pd.DataFrame, history_window: int = 90):
        """
        Khởi tạo với DataFrame đã được làm giàu.

        Args:
            feature_df (pd.DataFrame): DataFrame từ FeatureEngine.
            history_window (int): Số ngày lịch sử để xem xét cho các phân tích.
        """
        if feature_df.empty or len(feature_df) < history_window:
            raise ValueError(f"Input DataFrame must not be empty and have at least {history_window} rows.")
        
        self.df = feature_df
        # Lấy một cửa sổ dữ liệu để phân tích
        self.analysis_df = self.df.tail(history_window).copy()
        self.latest_row = self.analysis_df.iloc[-1]
        self.current_price = self.latest_row['close']
        
        self.history_window = history_window
        
    def identify_levels(self) -> Dict[str, List[Dict]]:
        """
        Hàm chính, tổng hợp các mức S/R từ nhiều phương pháp.
        """
        
        all_levels_with_source = []
        all_levels_with_source.extend(self._get_dynamic_levels_from_ma_bb())
        all_levels_with_source.extend(self._get_pivot_point_levels())
        all_levels_with_source.extend(self._get_simple_fibonacci_levels())
        
        support_objects = []
        resistance_objects = []
        
        for level, source in all_levels_with_source:
            level_obj = {"level": round(level, 2), "source": source}
            if level < self.current_price:
                support_objects.append(level_obj)
            else:
                resistance_objects.append(level_obj)
                
        return {
            "support": sorted(support_objects, key=lambda x: x['level'], reverse=True),
            "resistance": sorted(resistance_objects, key=lambda x: x['level']),
            "params": {
                "history_window": self.history_window
            }
        }

    # --- CÁC HÀM CỦA PHIÊN BẢN 1 ---
    
    def _get_dynamic_levels_from_ma_bb(self) -> List[Tuple[float, str]]:
        """
        Lấy các mức S/R động từ các đường MA và Bollinger Bands.
        Đây là các mức thay đổi mỗi ngày.
        """
        levels = []
        # Các cột cần trích xuất từ dòng dữ liệu cuối cùng
        dynamic_level_cols = [
            'SMA_20', 'SMA_50', 'SMA_200',
            'BBU_20_2.0', 'BBL_20_2.0', 'BBM_20_2.0'
        ]
        
        for col in dynamic_level_cols:
            if col in self.latest_row and pd.notna(self.latest_row[col]):
                levels.append((self.latest_row[col], col))
        
        return levels

    def _get_pivot_point_levels(self) -> List[Tuple[float, str]]:
        """
        Tính toán các mức Pivot Points cổ điển dựa trên dữ liệu của ngày hôm trước.
        """
        if len(self.analysis_df) < 2:
            return []
        
        prev_row = self.analysis_df.iloc[-2]
        H, L, C = prev_row['high'], prev_row['low'], prev_row['close']

        PP = (H + L + C) / 3
        R1 = (2 * PP) - L
        S1 = (2 * PP) - H
        R2 = PP + (H - L)
        S2 = PP - (H - L)
        R3 = H + 2 * (PP - L)
        S3 = L - 2 * (H - PP)
        
        names = [f'Pivot point {x}' for x in ['PP', 'R1', 'S1', 'R2', 'S2', 'R3', 'S3']]
        vals = [PP, R1, S1, R2, S2, R3, S3]
        
        levels = []
        for i in range(len(vals)):
            levels.append((vals[i], names[i]))
            
        return levels

    def _get_simple_fibonacci_levels(self) -> List[Tuple[float, float]]:
        """
        Phiên bản 1: Tính các mức Fibonacci Retracement dựa trên
        điểm cao nhất và thấp nhất trong cửa sổ phân tích.
        """
        # Xác định "con sóng" một cách đơn giản
        swing_high = self.analysis_df['high'].max()
        swing_low = self.analysis_df['low'].min()
        
        price_range = swing_high - swing_low
        if price_range == 0:
            return []

        # Các tỷ lệ Fibonacci kinh điển
        fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
        
        levels = []
        # Giả định một xu hướng tăng (tính các mức hỗ trợ)
        for ratio in fib_ratios:
            levels.append((swing_high - price_range * ratio, f'Fibonacci Ratio {ratio:.4f}'))
            
            # Thêm cả các mức mở rộng (có thể là kháng cự)
            levels.append((swing_high + price_range * ratio, f'Fibonacci Ratio {-ratio:.4f}'))
        
        return levels
    
    # --- CÁC HÀM PLACEHOLDER CHO PHIÊN BẢN 2 ---

    def _get_levels_from_extrema_v2(self, recognizer: Any = None) -> List[float]:
        """
        Phiên bản 2: Sẽ lấy các mức S/R tĩnh từ các đỉnh/đáy lịch sử
        do PatternRecognizer cung cấp.
        
        Args:
            recognizer: Một instance của PatternRecognizer.
        """
        # Trong phiên bản 1, hàm này không làm gì cả.
        # Nó là một placeholder cho việc nâng cấp trong tương lai.
        pass
        
        # --- VÍ DỤ VỀ CODE SẼ CÓ TRONG PHIÊN BẢN 2 ---
        # if recognizer is None:
        #     return []
        #
        # # Lấy các đỉnh và đáy từ recognizer
        # peaks = recognizer.peaks
        # troughs = recognizer.troughs
        #
        # # Mức giá của các đỉnh/đáy chính là các mức S/R
        # peak_prices = peaks['price'].tolist()
        # trough_prices = troughs['price'].tolist()
        #
        # return peak_prices + trough_prices
        
        return [] # Trả về danh sách rỗng trong v1
        
    def _get_advanced_fibonacci_levels_v2(self, recognizer: Any = None) -> List[float]:
        """
        Phiên bản 2: Sẽ tính Fibonacci dựa trên các đỉnh/đáy quan trọng
        thay vì chỉ dùng min/max.
        """
        # Placeholder cho phiên bản 2
        pass
        return []