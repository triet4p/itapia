from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from app.forecasting.task.ndays_distribution import NDaysDistributionTask, DISTRIBUTION_FEATURES

class PostProcessor(ABC):
        
    @abstractmethod
    def apply(self, raw_predict: np.ndarray) -> np.ndarray:
        pass
    
class NDaysDistributionPostProcessor(PostProcessor):
    def __init__(self, task: NDaysDistributionTask):
        self.task = task
        
    def apply(self, raw_predict):
        raw_df = pd.DataFrame(raw_predict, columns=self.task.targets)
        
        col_mapping = {col: col.split('_')[1] for col in raw_df.columns}
        raw_df.rename(mapper=col_mapping, inplace=True)
        
        if raw_df.columns.tolist() != DISTRIBUTION_FEATURES:
            raise ValueError('Column name not match')
        
        # Std >= 0
        raw_df['std'] = raw_df['std'].clip(lower=0)
        
        # Ràng buộc 1: min <= max, nếu ko thì min=max=(min+max)/2
        min_greater_max = raw_df['min'] > raw_df['max']
        if min_greater_max.any():
            mid = (raw_df.loc[min_greater_max, 'min'] + raw_df.loc[min_greater_max, 'max']) / 2
            raw_df.loc[min_greater_max, 'min'] = mid
            raw_df.loc[min_greater_max, 'max'] = mid
            
        # Ràng buộc 2: mean, q25, q75 nằm trong [min, max]
        raw_df['mean'] = raw_df['mean'].clip(raw_df['min'], raw_df['max'])
        raw_df['q25'] = raw_df['q25'].clip(raw_df['min'], raw_df['max'])
        raw_df['q75'] = raw_df['q75'].clip(raw_df['min'], raw_df['max'])
        
        # Ràng buộc 3: q25 <= q75
        q25_greater_q75 = raw_df['q25'] > raw_df['q75']
        if q25_greater_q75.any():
            mid_q = (raw_df.loc[q25_greater_q75, 'q25'] + raw_df.loc[q25_greater_q75, 'q75']) / 2
            raw_df.loc[q25_greater_q75, 'q25'] = mid_q
            raw_df.loc[q25_greater_q75, 'q75'] = mid_q
            
        return raw_df.to_numpy(copy=True)
    
class RoundingProcessor(PostProcessor):
    """Làm tròn các giá trị dự báo đến một số chữ số thập phân nhất định."""
    def __init__(self, decimals: int = 4):
        self.decimals = decimals

    def apply(self, raw_predict):
        return np.round(raw_predict, decimals=self.decimals)
        
        