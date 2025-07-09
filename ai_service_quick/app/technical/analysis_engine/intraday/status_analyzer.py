import pandas as pd
from typing import Dict, Any

class IntradayStatusAnalyzer:
    def __init__(self, feature_df: pd.DataFrame):
        self.df = feature_df
        self.latest_row = self.df.iloc[-1]
        
        # Lấy giá mở cửa của ngày hôm nay
        today_date = self.latest_row.name.date()
        self.opening_price = self.df[self.df.index.date == today_date]['open'].iloc[0]

    def analyze_current_status(self) -> Dict[str, Any]:
        current_price = self.latest_row['close']
        
        # 1. So sánh với VWAP
        vwap = self.latest_row.get('VWAP_D') # pandas-ta thường đặt tên VWAP là VWAP_D
        vwap_status = "Above" if vwap and current_price > vwap else "Below"
        
        # 2. So sánh với giá mở cửa
        open_status = "Positive" if current_price > self.opening_price else "Negative"
        
        # 3. Trạng thái RSI
        rsi = self.latest_row.get('RSI_14')
        rsi_status = "Neutral"
        if rsi:
            if rsi > 70: rsi_status = "Overbought"
            elif rsi < 30: rsi_status = "Oversold"
            
        return {
            "price_vs_vwap": vwap_status,
            "price_vs_open": open_status,
            "rsi_status": rsi_status,
            "evidence": {
                "current_price": round(current_price, 2),
                "vwap": round(vwap, 2) if vwap else None,
                "opening_price": round(self.opening_price, 2),
                "rsi_14": round(rsi, 2) if rsi else None
            }
        }