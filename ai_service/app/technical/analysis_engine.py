import pandas as pd
from typing import Dict

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
        
class AnalysisEngine:
    def __init__(self, feature_df: pd.DataFrame):
        if not isinstance(feature_df, pd.DataFrame) or feature_df.empty:
            raise ValueError("AnalysisEngine requires a non-empty pandas DataFrame.")
        self.df = feature_df
        self.latest_row = self.df.iloc[-1]
        self.trend_analyzer = TrendAnalyzer(self.df)
        
        # Init some other analyzer...
        
    def get_report(self):
        """
        Tạo báo cáo tình trạng kỹ thuật tổng hợp.
        """
        print("--- AnalysisEngine: Generating Full Analysis Report ---")
        
        # Không cần thay đổi ở đây, vì TrendAnalyzer đã đóng gói sự phức tạp bên trong
        trend_report = self.trend_analyzer.analyze_trend()
        
        # ... (logic cho patterns và support/resistance) ...

        report = {
            "indicators": self._extract_key_indicators(),
            "trend": trend_report,
            "patterns": ["Pending Implementation"],
            "support_resistance": {"support": [], "resistance": []},
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