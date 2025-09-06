from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from .task.ndays_distribution import NDaysDistributionTask, DISTRIBUTION_FEATURES

class PostProcessor(ABC):
        
    @abstractmethod
    def apply(self, raw_predict: np.ndarray) -> np.ndarray:
        """
        Apply post processor to a raw prediction and return processed prediction.
        """
        pass
    
class NDaysDistributionPostProcessor(PostProcessor):
    """Ensure that distribution prediction is reasonable. For example, `std>0` or `q25<=mean<=q75`"""
    def __init__(self, task: NDaysDistributionTask):
        self.task = task
        
    def apply(self, raw_predict):
        raw_df = pd.DataFrame(raw_predict, columns=self.task.targets)
        
        col_mapping = {col: col.split('_')[1] for col in raw_df.columns}
        raw_df.rename(mapper=col_mapping, axis=1, inplace=True)
        
        if set(raw_df.columns) != set(DISTRIBUTION_FEATURES):
            raise KeyError(
                f"Column name mismatch. Expected: {set(DISTRIBUTION_FEATURES)}, "
                f"Got: {set(raw_df.columns)}"
            )
        
        # Std >= 0
        raw_df['std'] = raw_df['std'].clip(lower=0)
        
        # min <= max, if no then min=max=(min+max)/2
        min_greater_max = raw_df['min'] > raw_df['max']
        if min_greater_max.any():
            mid = (raw_df.loc[min_greater_max, 'min'] + raw_df.loc[min_greater_max, 'max']) / 2
            raw_df.loc[min_greater_max, 'min'] = mid
            raw_df.loc[min_greater_max, 'max'] = mid
            
        #  mean, q25, q75 is in [min, max]
        raw_df['mean'] = raw_df['mean'].clip(raw_df['min'], raw_df['max'])
        raw_df['q25'] = raw_df['q25'].clip(raw_df['min'], raw_df['max'])
        raw_df['q75'] = raw_df['q75'].clip(raw_df['min'], raw_df['max'])
        
        #  q25 <= q75
        q25_greater_q75 = raw_df['q25'] > raw_df['q75']
        if q25_greater_q75.any():
            mid_q = (raw_df.loc[q25_greater_q75, 'q25'] + raw_df.loc[q25_greater_q75, 'q75']) / 2
            raw_df.loc[q25_greater_q75, 'q25'] = mid_q
            raw_df.loc[q25_greater_q75, 'q75'] = mid_q
            
        return raw_df.to_numpy(copy=True)
    
class DeNormalizationProcessor(PostProcessor):
    """
    Convert percentage forecasts (normalized) to absolute values ​​(de-normalized) based on a base price.
    """
    def __init__(self, base_prices: np.ndarray, task: NDaysDistributionTask):
        """
        Initialize the processor with a series of base prices.
        The index of base_prices must match the index of the forecast DataFrame.
        """
        if not isinstance(base_prices, np.ndarray):
            raise TypeError("base_prices must be a numpy array.")
        self.base_prices = base_prices
        self.task = task

    def apply(self, raw_predict: np.ndarray) -> np.ndarray:
 
        raw_df = pd.DataFrame(raw_predict, columns=self.task.targets)
        
        col_mapping = {col: col.split('_')[1] for col in raw_df.columns}
        raw_df.rename(mapper=col_mapping, axis=1, inplace=True)
        raw_df = raw_df / 100
        
        print("  - Applying DeNormalization Processor...")
        if len(self.base_prices) != len(raw_df):
            raise ValueError("Index of base_prices does not match prediction index.")
        
        print("  - Applying DeNormalization Processor (Vectorized)...")
    
        # Fhange to a column vector for broadcasting
        base_values = self.base_prices.reshape(-1, 1)

        std_cols = [col for col in raw_df.columns if 'std' in col]
        other_cols = [col for col in raw_df.columns if 'std' not in col]
        
        denorm_df = pd.DataFrame(index=raw_df.index)

        if std_cols:
            denorm_df[std_cols] = raw_df[std_cols] * base_values
        
        if other_cols:
            denorm_df[other_cols] = base_values * (1 + raw_df[other_cols])
            
        return denorm_df[self.task.targets].to_numpy()
    
class RoundingProcessor(PostProcessor):
    """Rounding processor"""
    def __init__(self, decimals: int = 4):
        self.decimals = decimals

    def apply(self, raw_predict):
        return np.round(raw_predict, decimals=self.decimals)
        
        