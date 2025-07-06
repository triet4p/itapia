import pandas as pd
from typing import Dict, Any, List
import numpy as np

class SupportResistanceIdentifier:
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

    def identify_levels(self) -> Dict[str, List[float]]:
        """
        Hàm chính, tổng hợp các mức S/R từ nhiều phương pháp.
        """
        print("--- SupportResistanceIdentifier: Identifying S/R Levels (v1) ---")
        
        # Tạo một tập hợp để chứa tất cả các mức và tự động loại bỏ trùng lặp
        all_levels = set()

        # --- Các phương pháp của phiên bản 1 ---
        all_levels.update(self._get_dynamic_levels_from_ma_bb())
        all_levels.update(self._get_pivot_point_levels())
        all_levels.update(self._get_simple_fibonacci_levels())
        
        # --- Các phương pháp sẽ có trong phiên bản 2 ---
        # Hàm này sẽ được nâng cấp khi có PatternRecognizer
        all_levels.update(self._get_levels_from_extrema_v2()) 
        
        # --- Phân loại và làm sạch kết quả ---
        support_levels = [level for level in all_levels if level < self.current_price]
        resistance_levels = [level for level in all_levels if level >= self.current_price]

        # Sắp xếp và làm tròn để kết quả đẹp hơn
        # Sắp xếp hỗ trợ từ cao đến thấp, kháng cự từ thấp đến cao
        return {
            "support": sorted(list(set(np.round(support_levels, 2))), reverse=True),
            "resistance": sorted(list(set(np.round(resistance_levels, 2))))
        }

    # --- CÁC HÀM CỦA PHIÊN BẢN 1 ---
    
    def _get_dynamic_levels_from_ma_bb(self) -> List[float]:
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
                levels.append(self.latest_row[col])
        
        return levels

    def _get_pivot_point_levels(self) -> List[float]:
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
        
        return [PP, R1, S1, R2, S2, R3, S3]

    def _get_simple_fibonacci_levels(self) -> List[float]:
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
            levels.append(swing_high - price_range * ratio)
            
        # Thêm cả các mức mở rộng (có thể là kháng cự)
        # levels.append(swing_high + price_range * 0.236)
        
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