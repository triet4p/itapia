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
        raw_df.rename(mapper=col_mapping, axis=1, inplace=True)
        
        if set(raw_df.columns) != set(DISTRIBUTION_FEATURES):
            raise ValueError(
                f"Column name mismatch. Expected: {set(DISTRIBUTION_FEATURES)}, "
                f"Got: {set(raw_df.columns)}"
            )
        
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
    
class DeNormalizationProcessor(PostProcessor):
    """
    Chuyển đổi các dự báo tỷ lệ phần trăm (normalized) thành các giá trị tuyệt đối
    (de-normalized) dựa trên một mức giá cơ sở.
    """
    def __init__(self, base_prices: np.ndarray, task: NDaysDistributionTask):
        """
        Khởi tạo processor với một chuỗi chứa các mức giá cơ sở.
        Index của base_prices phải khớp với index của DataFrame dự báo.
        """
        if not isinstance(base_prices, np.ndarray):
            raise TypeError("base_prices must be a numpy array.")
        self.base_prices = base_prices
        self.task = task

    def apply(self, raw_predict: np.ndarray) -> np.ndarray:
        """
        Áp dụng logic "giải bình thường hóa".
        """
        raw_df = pd.DataFrame(raw_predict, columns=self.task.targets)
        
        col_mapping = {col: col.split('_')[1] for col in raw_df.columns}
        raw_df.rename(mapper=col_mapping, axis=1, inplace=True)
        raw_df = raw_df / 100
        
        print("  - Applying DeNormalization Processor...")
        if len(self.base_prices) != len(raw_df):
            raise ValueError("Index of base_prices does not match prediction index.")
        
        print("  - Applying DeNormalization Processor (Vectorized)...")
    
        # Chuyển base_prices thành một vector cột để broadcasting
        base_values = self.base_prices.reshape(-1, 1)

        # Lấy ra các cột std và các cột còn lại
        std_cols = [col for col in raw_df.columns if 'std' in col]
        other_cols = [col for col in raw_df.columns if 'std' not in col]
        
        # Tạo một DataFrame kết quả
        denorm_df = pd.DataFrame(index=raw_df.index)

        # Áp dụng phép toán cho từng nhóm cột
        if std_cols:
            # Broadcasting: Nhân mỗi hàng trong raw_df[std_cols] với giá trị tương ứng trong base_values
            denorm_df[std_cols] = raw_df[std_cols] * base_values
        
        if other_cols:
            denorm_df[other_cols] = base_values * (1 + raw_df[other_cols])
            
        # Sắp xếp lại các cột theo đúng thứ tự ban đầu và trả về
        return denorm_df[self.task.targets].to_numpy()
    
class RoundingProcessor(PostProcessor):
    """Làm tròn các giá trị dự báo đến một số chữ số thập phân nhất định."""
    def __init__(self, decimals: int = 4):
        self.decimals = decimals

    def apply(self, raw_predict):
        return np.round(raw_predict, decimals=self.decimals)
        
        