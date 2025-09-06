"""Intraday key level identification engine."""

import pandas as pd
from typing import Dict

from itapia_common.schemas.entities.analysis.technical.intraday import KeyLevelsReport


class IntradayLevelIdentifier:
    """Identifies key intraday price levels."""
    
    def __init__(self, feature_df: pd.DataFrame):
        """Initialize with a feature-enriched DataFrame.
        
        Args:
            feature_df (pd.DataFrame): DataFrame with intraday features
        """
        self.df = feature_df
        # Get today's data for analysis
        today_date = self.df.index[-1].date()
        self.today_df = self.df[self.df.index.date == today_date]

    def identify_key_levels(self) -> KeyLevelsReport:
        """Aggregate important price levels for the day.
        
        Returns:
            KeyLevelsReport: Report containing key intraday price levels
        """
        levels = {}
        
        # Basic daily price levels
        levels['day_high'] = self.today_df['high'].max()
        levels['day_low'] = self.today_df['low'].min()
        levels['open_price'] = self.today_df['open'].iloc[0]
        
        # Levels from FeatureEngine
        latest_row = self.df.iloc[-1]
        levels['vwap'] = latest_row.get('VWAP_D')
        levels['or_30m_high'] = latest_row.get('OR_30m_High')  # From IntradayFeatureEngine
        levels['or_30m_low'] = latest_row.get('OR_30m_Low')

        # TODO: Integrate Pivot Points from daily analysis, as they are still valuable
        # This is not integrated here but will be integrated through the coordinator to ensure single responsibility.
        
        # Round and remove None values
        for k, v in levels.items():
            if v is not None:
                levels[k] = round(v, 2)
        
        return KeyLevelsReport.model_validate(levels)