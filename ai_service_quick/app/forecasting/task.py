# forecasting/task.py

import pandas as pd
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from datetime import datetime

from abc import ABC, abstractmethod
from typing import Literal, Dict, List

class _MLTask(ABC):
    def __init__(self, task_id: str, task_type: Literal['clf', 'reg'],
                 require_cdl_features: int = 7,
                 require_non_cdl_features: int = 45):
        self.task_id = task_id
        self.task_type = task_type
        
        self.targets: List[str] = []
        self.selected_features: List[str] = []
        self.non_cdl_features_cnt: int = require_non_cdl_features
        self.cdl_features_cnt: int = require_cdl_features
        
        self.target_for_selection: str = ""
        
        self.model = None
        self.model_name: str = None
        self.model_params: Dict = None
        
    def get_metadata(self) -> Dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "targets": self.targets,
            "target_for_selection": self.target_for_selection,
            "model_name": self.model_name,
            "model_params": self.model_params,
            "features": {
                "selected": self.selected_features,
                "cdl_features_cnt": self.cdl_features_cnt,
                "non_cdl_features_cnt": self.non_cdl_features_cnt
            }
        }
    
    @abstractmethod
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        pass
    
    def set_model(self, model_class, model_params: Dict, model_name: str):
        self.model = model_class(**model_params)
        self.model_name = model_name
        self.model_params = model_params
    
    def register_model_to_kaggle(self):
        if self.model is None:
            raise TypeError('Model could not null')
        
        today = datetime.now().strftime("%Y_%m_%d")
        model_identify = f'{self.model_name}-{today}-{self.task_id}'
        
        pass
    
    def load_model_from_kaggle(self, model_identify: str):
        pass
    
def get_triple_barrier_labels(prices: pd.Series, h: int, tp_pct: float, sl_pct: float) -> pd.Series:
    """
    Gán nhãn dựa trên phương pháp Triple-Barrier (Phiên bản cải tiến).

    Khởi tạo nhãn là NaN để phân biệt rõ ràng các điểm không thể gán nhãn
    (do thiếu dữ liệu tương lai) với các điểm có nhãn 0 (timeout).
    """
    # Khởi tạo chuỗi nhãn với NaN thay vì 0
    out = pd.Series(index=prices.index, data=np.nan, dtype=np.float16)

    # Tính toán các rào cản cho mỗi điểm thời gian
    upper_barrier = prices * (1 + tp_pct)
    lower_barrier = prices * (1 - sl_pct)

    # Vòng lặp chỉ chạy đến điểm mà chúng ta có đủ h ngày trong tương lai
    for i in range(len(prices) - h):
        future_window = prices.iloc[i + 1 : i + 1 + h]
        
        hit_tp = future_window[future_window >= upper_barrier.iloc[i]]
        hit_sl = future_window[future_window <= lower_barrier.iloc[i]]

        first_tp_time = hit_tp.index.min() if not hit_tp.empty else pd.NaT
        first_sl_time = hit_sl.index.min() if not hit_sl.empty else pd.NaT

        if pd.isna(first_tp_time) and pd.isna(first_sl_time):
            # Không chạm rào nào -> Timeout
            out.iloc[i] = 0
        elif pd.isna(first_sl_time) or first_tp_time < first_sl_time:
            # Chạm rào trên trước -> Win
            out.iloc[i] = 1
        else:
            # Chạm rào dưới trước -> Loss
            out.iloc[i] = -1
            
    # Ở bước này, h hàng cuối cùng của `out` sẽ là NaN.
    # Chúng ta có thể quyết định xử lý chúng như thế nào.
    # Lựa chọn tốt nhất là xóa chúng đi cùng với các features tương ứng
    # trước khi huấn luyện mô hình.
    
    # Hàm này chỉ trả về chuỗi có chứa NaN.
    # Việc xóa NaN sẽ được thực hiện ở bước sau.
    return out
    
def find_triple_barrier_optimal_params(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    base_price_col: str,
    horizons: list = [5, 10, 15],
    tp_pcts: list = [0.03, 0.05, 0.07],
    sl_pcts: list = [0.02, 0.03, 0.05]
) -> dict:
    """
    Tự động tìm bộ tham số Triple Barrier tối ưu bằng cách chạy grid search
    và chấm điểm các kết quả dựa trên các tiêu chí đã định nghĩa.

    Args:
        df_train (pd.DataFrame): DataFrame huấn luyện.
        df_test (pd.DataFrame): DataFrame kiểm tra (dữ liệu gần đây).
        horizons, tp_pcts, sl_pcts: Lưới các tham số để tìm kiếm.

    Returns:
        dict: Một dictionary chứa các tham số tốt nhất ('h', 'tp_pct', 'sl_pct').
    """
    print("--- Automatically finding optimal Triple Barrier parameters ---")
    results = []

    for h in horizons:
        for tp in tp_pcts:
            for sl in sl_pcts:
                if sl >= tp: continue

                # Gán nhãn trên cả hai tập
                train_labels = get_triple_barrier_labels(df_train[base_price_col], h, tp, sl).dropna()
                test_labels = get_triple_barrier_labels(df_test[base_price_col], h, tp, sl).dropna()
                
                if train_labels.empty or test_labels.empty: continue

                # Tính toán phân phối
                train_dist = train_labels.value_counts(normalize=True)
                test_dist = test_labels.value_counts(normalize=True)
                
                results.append({
                    'h': h, 'tp_pct': tp, 'sl_pct': sl,
                    'win_train': train_dist.get(1, 0), 'loss_train': train_dist.get(-1, 0), 'timeout_train': train_dist.get(0, 0),
                    'win_test': test_dist.get(1, 0), 'loss_test': test_dist.get(-1, 0), 'timeout_test': test_dist.get(0, 0)
                })

    if not results:
        raise ValueError("Grid search yielded no results. Check data and parameters.")

    results_df = pd.DataFrame(results)

    # --- HÀM ĐIỂM SỐ (SCORING FUNCTION) ---
    # 1. Điểm Cân bằng (Balance Score): Gần 1 là tốt nhất.
    #    Sử dụng tỷ lệ của lớp nhỏ nhất (win, loss) so với lớp lớn nhất.
    #    Chúng ta muốn tối đa hóa tỷ lệ của lớp thiểu số.
    results_df['balance_score'] = results_df[['win_train', 'loss_train']].min(axis=1) / results_df[['win_train', 'loss_train']].max(axis=1)

    # 2. Phạt Timeout (Timeout Penalty): Gần 1 là tốt nhất.
    #    Bị phạt mạnh khi timeout > 50%.
    results_df['actionability_score'] = 1 - results_df['timeout_train']
    # Phạt nặng hơn
    results_df.loc[results_df['timeout_train'] > 0.5, 'actionability_score'] *= 0.5 

    # 3. Phạt Bất ổn định (Stability Penalty): Gần 1 là tốt nhất.
    #    Đo chênh lệch tương đối giữa train và test.
    win_diff = abs(results_df['win_test'] - results_df['win_train']) / (results_df['win_train'] + 1e-9)
    loss_diff = abs(results_df['loss_test'] - results_df['loss_train']) / (results_df['loss_train'] + 1e-9)
    results_df['stability_score'] = 1 - (win_diff + loss_diff) / 2
    # Giới hạn điểm phạt, không để nó âm
    results_df['stability_score'] = results_df['stability_score'].clip(lower=0)
    
    # 4. Thưởng Risk/Reward (RR Bonus)
    results_df['rr_bonus'] = (results_df['tp_pct'] / results_df['sl_pct']).clip(upper=3) / 10 # Thưởng tối đa 0.3 điểm

    # --- TÍNH ĐIỂM CUỐI CÙNG (CÓ TRỌNG SỐ) ---
    weights = {
        'balance': 0.4,
        'actionability': 0.4,
        'stability': 0.2
    }
    results_df['final_score'] = (
        results_df['balance_score'] * weights['balance'] +
        results_df['actionability_score'] * weights['actionability'] +
        results_df['stability_score'] * weights['stability'] +
        results_df['rr_bonus']
    )
    
    # Sắp xếp và xem các ứng viên hàng đầu
    sorted_results = results_df.sort_values(by='final_score', ascending=False)
    print("\nTop 5 candidates based on automated scoring:")
    print(sorted_results.head(5)[['h', 'tp_pct', 'sl_pct', 'final_score', 'balance_score', 'actionability_score', 'stability_score']])
    
    # Lấy ra bộ tham số tốt nhất
    best_params_row = sorted_results.iloc[0]
    best_params = {
        'h': int(best_params_row['h']),
        'tp_pct': best_params_row['tp_pct'],
        'sl_pct': best_params_row['sl_pct']
    }
    
    print(f"\n==> Automatically selected best parameters: {best_params}")
    return best_params
    
class TripleBarrierTask(_MLTask):
    def __init__(self, task_id: str,
                 horizon: int,
                 tp_pct: float,
                 sl_pct: float,
                 require_cdl_features: int = 7,
                 require_non_cdl_features: int = 45):
        super().__init__(task_id, 'clf', require_cdl_features, require_non_cdl_features)
        self.horizon = horizon
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        
        self.targets = [f'target_tb_{horizon}d_{tp_pct*100:.0f}tp_{sl_pct*100:.0f}sl']
        self.targets_for_selection = self.targets[0]
        
    def get_metadata(self):
        _super_metadata = super().get_metadata()
        _super_metadata['horizon'] = self.horizon
        _super_metadata['tp_pct'] = self.tp_pct
        _super_metadata['sl_pct'] = self.sl_pct
        
        return _super_metadata
    
    def create_targets(self, df: pd.DataFrame, base_price_col: str):
        prices = df[base_price_col]
        target_labels = get_triple_barrier_labels(prices, self.horizon,
                                                  self.tp_pct, self.sl_pct)
        return target_labels.to_frame(name=self.targets[0])
    
    
class NDaysDistributionTask(_MLTask):
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
    
    def create_targets(self, df, base_price_col):
        prices = df[base_price_col]
        targets = pd.DataFrame(index=prices.index)
        price_vals = prices.values
        
        # Tạo một view 2D của tất cả các cửa sổ tương lai có thể
        # Ví dụ: [[p1,p2,p3], [p2,p3,p4], [p3,p4,p5], ...]
        future_windows = sliding_window_view(price_vals, window_shape=self.horizon)
        
        # Dữ liệu của chúng ta là các cửa sổ BẮT ĐẦU từ ngày mai
        # Nên chúng ta cần dịch chuyển kết quả tính toán đi 1 bước
        
        num_predictions = len(price_vals) - self.horizon
        
        if num_predictions <= 0:
            return targets # Không đủ dữ liệu
            
        # Lấy các cửa sổ tương lai cho mỗi điểm (từ t+1 đến t+horizon)
        # Cửa sổ cho ngày 0 là từ ngày 1 đến ngày horizon
        # Cửa sổ cho ngày cuối cùng có thể dự báo là từ...
        windows_for_prediction = future_windows[1 : num_predictions + 1]
        
        # Tính toán trên toàn bộ các cửa sổ cùng lúc
        targets[f'target_mean_{self.horizon}d'] = np.nan
        targets[f'target_std_{self.horizon}d'] = np.nan
        targets[f'target_min_{self.horizon}d'] = np.nan
        targets[f'target_max_{self.horizon}d'] = np.nan
        targets[f'target_q25_{self.horizon}d'] = np.nan
        targets[f'target_q75_{self.horizon}d'] = np.nan

        targets.iloc[:num_predictions, 0] = np.mean(windows_for_prediction, axis=1)
        targets.iloc[:num_predictions, 1] = np.std(windows_for_prediction, axis=1)
        targets.iloc[:num_predictions, 2] = np.min(windows_for_prediction, axis=1)
        targets.iloc[:num_predictions, 3] = np.max(windows_for_prediction, axis=1)
        targets.iloc[:num_predictions, 4] = np.quantile(windows_for_prediction, 0.25, axis=1)
        targets.iloc[:num_predictions, 5] = np.quantile(windows_for_prediction, 0.75, axis=1)
        
        return targets