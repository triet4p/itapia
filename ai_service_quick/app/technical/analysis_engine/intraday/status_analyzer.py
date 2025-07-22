import pandas as pd
from typing import Dict, Any

from itapia_common.dblib.schemas.reports.technical_analysis.intraday import CurrentStatusReport

class IntradayStatusAnalyzer:
    def __init__(self, feature_df: pd.DataFrame):
        self.df = feature_df
        self.latest_row = self.df.iloc[-1]
        
        # Lấy giá mở cửa của ngày hôm nay
        today_date = self.latest_row.name.date()
        self.opening_price = self.df[self.df.index.date == today_date]['open'].iloc[0]

    def analyze_current_status(self):
        current_price = self.latest_row['close']
        
        # 1. So sánh với VWAP
        vwap = self.latest_row.get('VWAP_D') # pandas-ta thường đặt tên VWAP là VWAP_D
        vwap_status = 'undefined'
        if vwap:
            vwap_status = "above" if current_price > vwap else "below"
        
        # 2. So sánh với giá mở cửa
        open_status = "above" if current_price > self.opening_price else "below"
        
        # 3. Trạng thái RSI
        rsi = self.latest_row.get('RSI_14')
        rsi_status = "neutral"
        if rsi:
            if rsi > 70: rsi_status = "overbought"
            elif rsi < 30: rsi_status = "oversold"
        
        return CurrentStatusReport(
            vwap_status=vwap_status,
            open_status=open_status,
            rsi_status=rsi_status,
            evidence={
                "current_price": round(current_price, 2),
                "vwap": round(vwap, 2) if vwap else None,
                "opening_price": round(self.opening_price, 2),
                "rsi_14": round(rsi, 2) if rsi else None
            }
        )