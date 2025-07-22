import pandas as pd
from typing import Dict

from itapia_common.dblib.schemas.reports.technical_analysis.intraday import KeyLevelsReport

class IntradayLevelIdentifier:
    def __init__(self, feature_df: pd.DataFrame):
        self.df = feature_df
        # Lấy dữ liệu của chỉ ngày hôm nay để phân tích
        today_date = self.df.index[-1].date()
        self.today_df = self.df[self.df.index.date == today_date]

    def identify_key_levels(self):
        """
        Tổng hợp các mức giá quan trọng trong ngày.
        """
        levels = {}
        
        # Các mức giá cơ bản trong ngày
        levels['day_high'] = self.today_df['high'].max()
        levels['day_low'] = self.today_df['low'].min()
        levels['open_price'] = self.today_df['open'].iloc[0]
        
        # Các mức từ FeatureEngine
        latest_row = self.df.iloc[-1]
        levels['vwap'] = latest_row.get('VWAP_D')
        levels['or_30m_high'] = latest_row.get('OR_30m_High') # Từ IntradayFeatureEngine
        levels['or_30m_low'] = latest_row.get('OR_30m_Low')

        # TODO: Tích hợp Pivot Points từ phân tích hàng ngày, vì chúng vẫn rất giá trị
        # Cái này ko tích hợp ở đây mà sẽ được tích hợp qua bộ điều phối để đảm bảo đơn trách nhiệm.
        
        # Làm tròn và loại bỏ giá trị None
        for k, v in levels.items():
            if v is not None:
                levels[k] = round(v, 2)
        
        return KeyLevelsReport.model_validate(levels)