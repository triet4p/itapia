import pandas as pd
from typing import Dict, Any

from itapia_common.schemas.entities.reports.technical.intraday import MomentumReport

class IntradayMomentumAnalyzer:
    def __init__(self, feature_df: pd.DataFrame):
        self.df = feature_df
        self.latest_row = self.df.iloc[-1]
        
    def analyze_momentum_and_volume(self):
        # 1. Phân tích MACD
        macd_line = self.latest_row.get('MACD_12_26_9')
        signal_line = self.latest_row.get('MACDs_12_26_9')
        macd_crossover = "neutral"
        if macd_line and signal_line:
            if macd_line > signal_line: macd_crossover = "bull"
            else: macd_crossover = "bear"
            
        # 2. Phân tích Volume Spike
        # So sánh khối lượng của cây nến cuối cùng với trung bình 10 cây nến trước đó
        avg_volume = self.df['volume'].iloc[-11:-1].mean()
        current_volume = self.latest_row['volume']
        volume_spike_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        volume_status = "normal"
        if volume_spike_ratio > 2.0: # Gấp đôi mức trung bình
            volume_status = "high-spike"
            
        # 3. Phân tích Opening Range Breakout
        or_high = self.latest_row.get('OR_30m_High')
        or_low = self.latest_row.get('OR_30m_Low')
        breakout_status = "inside"
        if or_high and or_low:
            if self.latest_row['close'] > or_high:
                breakout_status = "bull-breakout"
            elif self.latest_row['close'] < or_low:
                breakout_status = "bear-breakdown"
        
        return MomentumReport(
            macd_crossover=macd_crossover,
            volume_status=volume_status,
            opening_range_status=breakout_status,
            evidence={
                "current_volume": int(current_volume),
                "avg_10_period_volume": int(avg_volume),
                "volume_spike_ratio": round(volume_spike_ratio, 2)
            }
        )