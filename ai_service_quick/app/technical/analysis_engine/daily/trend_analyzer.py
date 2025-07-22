import pandas as pd
from typing import Dict

from itapia_common.dblib.schemas.reports.technical_analysis.daily import MidTermTrendReport, \
    LongTermTrendReport, OverallStrengthTrendReport, TrendReport

class DailyTrendAnalyzer:
    def __init__(self, feature_df: pd.DataFrame):
        if feature_df.empty:
            raise ValueError("Input DataFrame for TrendAnalyzer cannot be empty.")
        
        self.df = feature_df
        self.latest_row = self.df.iloc[-1]
        
    def _analyze_ma_trend(self, short_ma_col: str, long_ma_col: str):
        if short_ma_col not in self.latest_row or long_ma_col not in self.latest_row:
            return "undefined"
        
        if self.latest_row[short_ma_col] > self.latest_row[long_ma_col]:
            return "uptrend"
        else:
            return "downtrend"
        
    def _get_adx_strength(self, adx_col: str):
        if adx_col not in self.latest_row:
            return OverallStrengthTrendReport(
                strength='undefined',
                value=0
            )
        
        adx_val = self.latest_row[adx_col]
        if adx_val > 25:
            return OverallStrengthTrendReport(
                strength='strong', 
                value=adx_val
            )
        elif adx_val >= 20:
            return OverallStrengthTrendReport(
                strength='moderate', 
                value=adx_val
            )
        else:
            return OverallStrengthTrendReport(
                strength='weak', 
                value=adx_val
            )
        
    def _get_adx_direction(self, dmp_col: str, dmn_col: str):
        if dmp_col not in self.latest_row or dmn_col not in self.latest_row: 
            return "undefined"
        return "uptrend" if self.latest_row[dmp_col] > self.latest_row[dmn_col] else "downtrend"
    
    def _get_mid_term_view(self):
        # Cặp MA phù hợp cho trung hạn 20/50
        short_ma = 'SMA_20'
        long_ma = 'SMA_50'
        trend_direction = self._analyze_ma_trend(short_ma, long_ma)
        
        evidence = {
            "short_ma_name": short_ma,
            "short_ma_value": round(self.latest_row.get(short_ma, 0), 2),
            "long_ma_name": long_ma,
            "long_ma_value": round(self.latest_row.get(long_ma, 0), 2)
        }
        
        # Kiểm tra vị trí giá so với MA trung hạn
        ma_status = "undefined"
        if 'close' in self.latest_row and 'SMA_50' in self.latest_row:
            if self.latest_row['close'] > self.latest_row['SMA_50']:
                ma_status = "positive" # Tích cực
            else:
                ma_status = "negative" # Chịu áp lực
        
        # Phân tích ADX để xem hướng đi hiện tại
        adx_direction = self._get_adx_direction('DMP_14', 'DMN_14')

        return MidTermTrendReport(
            ma_direction=trend_direction,
            ma_status=ma_status,
            adx_direction=adx_direction,
            evidence=evidence
        )
    
    def _get_long_term_view(self):
        """Phân tích xu hướng dài hạn (vài tháng đến một năm)."""
        # Cặp MA kinh điển 50/200
        short_ma = 'SMA_50'
        long_ma = 'SMA_200'
        trend_direction = self._analyze_ma_trend(short_ma, long_ma)
        
        evidence = {
            "short_ma_name": short_ma,
            "short_ma_value": round(self.latest_row.get(short_ma, 0), 2),
            "long_ma_name": long_ma,
            "long_ma_value": round(self.latest_row.get(long_ma, 0), 2)
        }
        
        # Kiểm tra vị trí giá so với MA dài hạn
        status = "Undefined"
        if 'close' in self.latest_row and 'SMA_200' in self.latest_row:
            if self.latest_row['close'] > self.latest_row['SMA_200']:
                status = "positive"
            else:
                status = "negative"

        return LongTermTrendReport(
            ma_direction=trend_direction,
            ma_status=status,
            evidence=evidence
        )
    
    def analyze_trend(self):
        """
        Thực hiện phân tích xu hướng toàn diện và trả về một dictionary đa chiều.
        """
        # Phân tích từng khung thời gian một cách độc lập
        long_term_analysis = self._get_long_term_view()
        mid_term_analysis = self._get_mid_term_view()
        
        # Sức mạnh xu hướng tổng thể được đo bằng ADX(14) tiêu chuẩn
        adx_strength = self._get_adx_strength('ADX_14')
        
        # --- Logic tổng hợp ---
        # "Primary" trend được định nghĩa là xu hướng trung hạn,
        # vì đó là mục tiêu chính của dự án.
        # Tuy nhiên, báo cáo vẫn chứa đầy đủ thông tin dài hạn.
        
        return TrendReport(
            primary_focus='mid-term',
            midterm_report=mid_term_analysis,
            longterm_report=long_term_analysis,
            overall_strength=adx_strength
        )
        
