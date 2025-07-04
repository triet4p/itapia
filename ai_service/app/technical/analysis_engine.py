import pandas as pd
from typing import Dict, List, Any
import numpy as np

class TrendAnalyzer:
    def __init__(self, feature_df: pd.DataFrame):
        if feature_df.empty:
            raise ValueError("Input DataFrame for TrendAnalyzer cannot be empty.")
        
        self.df = feature_df
        self.latest_row = self.df.iloc[-1]
        
    def _analyze_ma_trend(self, short_ma_col: str, long_ma_col: str) -> str:
        if short_ma_col not in self.latest_row or long_ma_col not in self.latest_row:
            return "Undefined"
        
        if self.latest_row[short_ma_col] > self.latest_row[long_ma_col]:
            return "Uptrend"
        else:
            return "Downtrend"
        
    def _get_adx_strength(self, adx_col: str) -> str:
        if adx_col not in self.latest_row:
            return "Undefined"
        
        adx_val = self.latest_row[adx_col]
        if adx_val > 25:
            return "Strong"
        elif adx_val >= 20:
            return "Moderate"
        else:
            return "Weak"
        
    def _get_adx_direction(self, dmp_col: str, dmn_col: str) -> str:
        if dmp_col not in self.latest_row or dmn_col not in self.latest_row: 
            return "Undefined"
        return "Up" if self.latest_row[dmp_col] > self.latest_row[dmn_col] else "Down"
    
    def _get_medium_term_view(self) -> Dict[str, str]:
        # Cặp MA phù hợp cho trung hạn 20/50
        trend_direction = self._analyze_ma_trend('SMA_20', 'SMA_50')
        
        # Kiểm tra vị trí giá so với MA trung hạn
        status = "Undefined"
        if 'close' in self.latest_row and 'SMA_50' in self.latest_row:
            if self.latest_row['close'] > self.latest_row['SMA_50']:
                status = "Constructive" # Tích cực
            else:
                status = "Under Pressure" # Chịu áp lực
        
        # Phân tích ADX để xem hướng đi hiện tại
        adx_direction = self._get_adx_direction('DMP_14', 'DMN_14')

        return {"direction": trend_direction, "status": status, "adx_direction": adx_direction}
    
    def _get_long_term_view(self) -> Dict[str, str]:
        """Phân tích xu hướng dài hạn (vài tháng đến một năm)."""
        # Cặp MA kinh điển 50/200
        trend_direction = self._analyze_ma_trend(short_ma_col='SMA_50', long_ma_col='SMA_200')
        
        # Kiểm tra vị trí giá so với MA dài hạn
        status = "Undefined"
        if 'close' in self.latest_row and 'SMA_200' in self.latest_row:
            if self.latest_row['close'] > self.latest_row['SMA_200']:
                status = "Above key moving average"
            else:
                status = "Below key moving average"

        return {"direction": trend_direction, "status": status}
    
    def analyze_trend(self):
        """
        Thực hiện phân tích xu hướng toàn diện và trả về một dictionary đa chiều.
        """
        # Phân tích từng khung thời gian một cách độc lập
        long_term_analysis = self._get_long_term_view()
        medium_term_analysis = self._get_medium_term_view()
        
        # Sức mạnh xu hướng tổng thể được đo bằng ADX(14) tiêu chuẩn
        adx_strength = self._get_adx_strength('ADX_14')
        
        # --- Logic tổng hợp ---
        # "Primary" trend được định nghĩa là xu hướng trung hạn,
        # vì đó là mục tiêu chính của dự án.
        # Tuy nhiên, báo cáo vẫn chứa đầy đủ thông tin dài hạn.
        
        return {
            "primary_focus": "Medium-Term", # Chỉ rõ trọng tâm phân tích
            "long_term": long_term_analysis,
            "medium_term": medium_term_analysis,
            "overall_strength": adx_strength # Sức mạnh chung của xu hướng hiện tại
        }

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
        
class AnalysisEngine:
    """
    Facade: Phân tích một DataFrame đã có đặc trưng và tạo ra một báo cáo.
    Nó điều phối các lớp chuyên gia để thực hiện các phân tích phức tạp.
    """
    def __init__(self, feature_df: pd.DataFrame, history_window: int = 90):
        """
        Khởi tạo với DataFrame đã được làm giàu bởi FeatureEngine.

        Args:
            feature_df (pd.DataFrame): DataFrame chứa các đặc trưng.
            history_window (int): Số ngày lịch sử để các analyzer xem xét.
        """
        if not isinstance(feature_df, pd.DataFrame) or feature_df.empty:
            raise ValueError("AnalysisEngine requires a non-empty pandas DataFrame.")
        
        self.df = feature_df
        # Lấy dòng dữ liệu cuối cùng để phân tích tình trạng hiện tại
        self.latest_row = self.df.iloc[-1]
        
        # --- KHỞI TẠO CÁC CHUYÊN GIA ---
        # Mỗi chuyên gia sẽ nhận DataFrame và tự xử lý phần dữ liệu nó cần.
        self.trend_analyzer = TrendAnalyzer(self.df)
        self.sr_identifier = SupportResistanceIdentifier(self.df, history_window=history_window)
        # self.pattern_recognizer = PatternRecognizer(self.df) # Sẽ thêm sau

    def get_analysis_report(self) -> Dict[str, Any]:
        """
        Tạo báo cáo tình trạng kỹ thuật tổng hợp bằng cách gọi các chuyên gia.
        """
        print("--- AnalysisEngine: Generating Full Analysis Report ---")
        
        # --- GỌI CÁC CHUYÊN GIA ĐỂ LẤY KẾT QUẢ PHÂN TÍCH ---
        trend_report = self.trend_analyzer.analyze_trend()
        sr_report = self.sr_identifier.identify_levels()
        
        # Tạm thời dùng giá trị placeholder cho module chưa có
        patterns_report = ["Pending Implementation"] 
        # Sau này sẽ thay thế bằng:
        # patterns_report = self.pattern_recognizer.find_patterns()

        # --- TỔNG HỢP THÀNH BÁO CÁO CUỐI CÙNG ---
        report = {
            "indicators": self._extract_key_indicators(),
            "trend": trend_report,
            "support_resistance": sr_report,
            "patterns": patterns_report,
        }
        return report

    def _extract_key_indicators(self) -> Dict[str, float]:
        """
        Trích xuất các giá trị chỉ báo quan trọng để hỗ trợ cả phân tích trung và dài hạn.
        """
        # Đảm bảo có tất cả các MA cần thiết: 20, 50, 200
        indicators_to_extract = [
            'SMA_20', 'SMA_50', 'SMA_200', 
            'RSI_14', 'ADX_14', 'DMP_14', 'DMN_14',
            'BBU_20_2.0', 'BBL_20_2.0', 'ATR_14'
        ]
        
        print("Extracting key indicators for multi-timeframe analysis...")
        key_indicators = {}
        for indicator in indicators_to_extract:
            if indicator in self.latest_row and pd.notna(self.latest_row[indicator]):
                key_indicators[indicator] = round(self.latest_row[indicator], 2)
            else:
                key_indicators[indicator] = None
                
        return key_indicators