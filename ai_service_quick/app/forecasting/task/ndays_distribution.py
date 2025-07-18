import pandas as pd
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from app.forecasting.task import ForecastingTask

def create_distribution_targets(prices: pd.Series, horizon: int) -> pd.DataFrame:
    """Phiên bản Vectorized sử dụng numpy để tránh vòng lặp for."""
    
    targets = pd.DataFrame(index=prices.index)
    price_vals = prices.values
    
    # Tạo một view 2D của tất cả các cửa sổ tương lai có thể
    # Ví dụ: [[p1,p2,p3], [p2,p3,p4], [p3,p4,p5], ...]
    future_windows = sliding_window_view(price_vals, window_shape=horizon)
    
    # Dữ liệu của chúng ta là các cửa sổ BẮT ĐẦU từ ngày mai
    # Nên chúng ta cần dịch chuyển kết quả tính toán đi 1 bước
    
    num_predictions = len(price_vals) - horizon
    
    if num_predictions <= 0:
        return targets # Không đủ dữ liệu
        
    # Lấy các cửa sổ tương lai cho mỗi điểm (từ t+1 đến t+horizon)
    # Cửa sổ cho ngày 0 là từ ngày 1 đến ngày horizon
    # Cửa sổ cho ngày cuối cùng có thể dự báo là từ...
    windows_for_prediction = future_windows[1 : num_predictions + 1]
    
    # Tính toán trên toàn bộ các cửa sổ cùng lúc
    targets[f'target_mean_{horizon}d'] = np.nan
    targets[f'target_std_{horizon}d'] = np.nan
    targets[f'target_min_{horizon}d'] = np.nan
    targets[f'target_max_{horizon}d'] = np.nan
    targets[f'target_q25_{horizon}d'] = np.nan
    targets[f'target_q75_{horizon}d'] = np.nan

    targets.iloc[:num_predictions, 0] = np.mean(windows_for_prediction, axis=1)
    targets.iloc[:num_predictions, 1] = np.std(windows_for_prediction, axis=1)
    targets.iloc[:num_predictions, 2] = np.min(windows_for_prediction, axis=1)
    targets.iloc[:num_predictions, 3] = np.max(windows_for_prediction, axis=1)
    targets.iloc[:num_predictions, 4] = np.quantile(windows_for_prediction, 0.25, axis=1)
    targets.iloc[:num_predictions, 5] = np.quantile(windows_for_prediction, 0.75, axis=1)
    
    return targets
    
class NDaysDistributionTask(ForecastingTask):
    def __init__(self, task_id: str,
                 horizon: int,
                 require_cdl_features: int = 7,
                 require_non_cdl_features: int = 45):
        super().__init__(task_id, 'reg', require_cdl_features, require_non_cdl_features)
        self.horizon = horizon
        
        self.targets = [f'target_{s}_{horizon}d' for s in ['mean', 'std', 'min', 'max', 'q25', 'q75']]
        self.target_for_selection = f'target_mean_{horizon}d'
        
    def get_metadata(self):
        _super_metadata = super().get_metadata()
        _super_metadata['horizon'] = self.horizon
        
        return _super_metadata
    
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        if 'ticker' not in df.columns:
            raise ValueError("DataFrame must have a 'ticker' column for group-aware target creation.")

        all_targets = []
        for _, group in df.groupby('ticker'):
            targets = create_distribution_targets(group[base_price_col], self.horizon)
            all_targets.append(targets)
        
        return pd.concat(all_targets)