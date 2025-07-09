import pandas as pd
from typing import Dict, Any

class IntradayMomentumAnalyzer:
    def __init__(self, feature_df: pd.DataFrame):
        self.df = feature_df
        self.latest_row = self.df.iloc[-1]
        
    def analyze_momentum_and_volume(self) -> Dict[str, Any]:
        # 1. Phân tích MACD
        macd_line = self.latest_row.get('MACD_12_26_9')
        signal_line = self.latest_row.get('MACDs_12_26_9')
        macd_crossover = "Neutral"
        if macd_line and signal_line:
            if macd_line > signal_line: macd_crossover = "Bullish"
            else: macd_crossover = "Bearish"
            
        # 2. Phân tích Volume Spike
        # So sánh khối lượng của cây nến cuối cùng với trung bình 10 cây nến trước đó
        avg_volume = self.df['volume'].iloc[-11:-1].mean()
        current_volume = self.latest_row['volume']
        volume_spike_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        volume_status = "Normal"
        if volume_spike_ratio > 2.0: # Gấp đôi mức trung bình
            volume_status = "High Volume Spike"
            
        # 3. Phân tích Opening Range Breakout
        or_high = self.latest_row.get('OR_30m_High')
        or_low = self.latest_row.get('OR_30m_Low')
        breakout_status = "Inside Range"
        if or_high and or_low:
            if self.latest_row['close'] > or_high:
                breakout_status = "Bullish Breakout"
            elif self.latest_row['close'] < or_low:
                breakout_status = "Bearish Breakdown"

        return {
            "macd_crossover": macd_crossover,
            "volume_status": volume_status,
            "opening_range_status": breakout_status,
            "evidence": {
                "current_volume": int(current_volume),
                "avg_10_period_volume": int(avg_volume),
                "volume_spike_ratio": round(volume_spike_ratio, 2)
            }
        }