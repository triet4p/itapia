"""Intraday status analysis engine."""

import pandas as pd
from typing import Dict, Any

from itapia_common.schemas.entities.analysis.technical.intraday import CurrentStatusReport


class IntradayStatusAnalyzer:
    """Analyzes current intraday market status relative to key benchmarks."""
    
    def __init__(self, feature_df: pd.DataFrame):
        """Initialize with a feature-enriched DataFrame.
        
        Args:
            feature_df (pd.DataFrame): DataFrame with intraday features
        """
        self.df = feature_df
        self.latest_row = self.df.iloc[-1]
        
        # Get today's opening price
        today_date = self.latest_row.name.date()
        self.opening_price = self.df[self.df.index.date == today_date]['open'].iloc[0]

    def analyze_current_status(self) -> CurrentStatusReport:
        """Analyze current market status relative to key benchmarks.
        
        Returns:
            CurrentStatusReport: Report containing current market status analysis
        """
        current_price = self.latest_row['close']
        
        # 1. Compare with VWAP
        vwap = self.latest_row.get('VWAP_D')  # pandas-ta typically names VWAP as VWAP_D
        vwap_status = 'undefined'
        if vwap:
            vwap_status = "above" if current_price > vwap else "below"
        
        # 2. Compare with opening price
        open_status = "above" if current_price > self.opening_price else "below"
        
        # 3. RSI Status
        rsi = self.latest_row.get('RSI_14')
        rsi_status = "neutral"
        if rsi:
            if rsi > 70: 
                rsi_status = "overbought"
            elif rsi < 30: 
                rsi_status = "oversold"
        
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