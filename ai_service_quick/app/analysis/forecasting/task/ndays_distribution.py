import pandas as pd
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from ._task import ForecastingTask

from itapia_common.schemas.entities.analysis.forecasting import NDaysDistributionTaskMetadata

DISTRIBUTION_FEATURES = ['mean', 'std', 'min', 'max', 'q25', 'q75']

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
                 horizon: int = 5,
                 require_cdl_features: int = 7,
                 require_non_cdl_features: int = 45):
        super().__init__(task_id, 'reg', 'percent', require_cdl_features, require_non_cdl_features)
        self.horizon = horizon
        
        self.targets = [f'target_{s}_pct_{horizon}d' for s in DISTRIBUTION_FEATURES]
        self.target_for_selection = f'target_mean_pct_{horizon}d'
        
    def get_metadata(self):
        _super_metadata = super().get_metadata()
        _super_metadata['horizon'] = self.horizon
        
        return _super_metadata
    
    def get_metadata_for_plain(self) -> NDaysDistributionTaskMetadata:
        return NDaysDistributionTaskMetadata(
            targets=self.targets,
            units=self.target_units,
            horizon=self.horizon
        )
    
    def load_metadata(self, task_meta):
        super().load_metadata(task_meta)
        self.horizon = int(task_meta['horizon'])
    
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        if 'ticker' not in df.columns:
            raise ValueError("DataFrame must have a 'ticker' column for group-aware target creation.")

        all_targets = []
        for _, group in df.groupby('ticker'):
            prices = group[base_price_col]
            
            # 1. Tính toán các target giá trị tuyệt đối như cũ
            abs_targets = create_distribution_targets(prices, self.horizon)
            
            # 2. BÌNH THƯỜNG HÓA (NORMALIZE)
            # Lấy giá đóng cửa hiện tại để làm mẫu số
            current_close = prices
            
            # Tạo DataFrame mới để chứa các target đã bình thường hóa
            norm_targets = pd.DataFrame(index=abs_targets.index)
            
            # Bình thường hóa mean, min, max, q25, q75 thành % thay đổi
            for stat in ['mean', 'min', 'max', 'q25', 'q75']:
                col_name = f'target_{stat}_{self.horizon}d'
                norm_targets[f'target_{stat}_pct_{self.horizon}d'] = \
                    ((abs_targets[col_name] - current_close) / current_close) * 100
            
            # Bình thường hóa std thành % so với giá hiện tại
            col_std = f'target_std_{self.horizon}d'
            norm_targets[f'target_std_pct_{self.horizon}d'] = \
                (abs_targets[col_std] / current_close) * 100

            all_targets.append(norm_targets)
        
        return pd.concat(all_targets)