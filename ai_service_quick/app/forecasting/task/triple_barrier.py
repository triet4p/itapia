import pandas as pd
import numpy as np
from app.forecasting.task import ForecastingTask

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

def generate_adaptive_grid(atr_percent):
    # atr_percent là biến động trung bình hàng ngày
    # Một mục tiêu hợp lý có thể là từ 3 đến 10 lần biến động hàng ngày
    
    # tp_pcts sẽ là bội số của atr_percent
    tp_multipliers = [3, 5, 8, 12] 
    tp_pcts = [round(atr_percent * m, 3) for m in tp_multipliers]

    # sl_pcts sẽ là một phần của tp_pcts
    sl_ratios = [0.5, 0.67] 
    sl_pcts = []
    for tp in tp_pcts:
        for ratio in sl_ratios:
            sl_pcts.append(round(tp * ratio, 3))
    
    # Loại bỏ trùng lặp và sắp xếp
    tp_pcts = sorted(list(set(tp_pcts)))
    sl_pcts = sorted(list(set(sl_pcts)))

    # horizons có thể vẫn giữ nguyên
    horizons = [5, 10, 15, 20]
    
    return {"horizons": horizons, "tp_pcts": tp_pcts, "sl_pcts": sl_pcts}
    
def find_triple_barrier_optimal_params(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    base_price_col: str,
    horizons: list,
    tp_pcts: list,
    sl_pcts: list
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

    print(f"--- Generating Grid result with {len(horizons)*len(tp_pcts)*len(sl_pcts)} candidates ---")
    cnt = 0
    for h in horizons:
        for tp in tp_pcts:
            for sl in sl_pcts:
                cnt += 1
                if sl >= tp: 
                    continue

                # Gán nhãn trên cả hai tập
                # --- SỬA LỖI: Áp dụng get_triple_barrier_labels cho từng nhóm ticker ---
                train_labels_list = [get_triple_barrier_labels(group[base_price_col], h, tp, sl) for _, group in df_train.groupby('ticker')]
                train_labels = pd.concat(train_labels_list).dropna()

                test_labels_list = [get_triple_barrier_labels(group[base_price_col], h, tp, sl) for _, group in df_test.groupby('ticker')]
                test_labels = pd.concat(test_labels_list).dropna()
                # --- KẾT THÚC SỬA LỖI ---
                
                if train_labels.empty or test_labels.empty: continue

                # Tính toán phân phối
                train_dist = train_labels.value_counts(normalize=True)
                test_dist = test_labels.value_counts(normalize=True)
                
                results.append({
                    'h': h, 'tp_pct': tp, 'sl_pct': sl,
                    'win_train': train_dist.get(1, 0), 'loss_train': train_dist.get(-1, 0), 'timeout_train': train_dist.get(0, 0),
                    'win_test': test_dist.get(1, 0), 'loss_test': test_dist.get(-1, 0), 'timeout_test': test_dist.get(0, 0)
                })
                
                if cnt % 10 == 0: 
                    print(f"--- Generated {cnt}/{len(horizons)*len(tp_pcts)*len(sl_pcts)} candidates")

    if not results:
        raise ValueError("Grid search yielded no results. Check data and parameters.")

    results_df = pd.DataFrame(results)

    # --- HÀM ĐIỂM SỐ (SCORING FUNCTION) ---
    # 1. Điểm Cân bằng (Balance Score): Gần 1 là tốt nhất.
    #    Sử dụng tỷ lệ của lớp nhỏ nhất (win, loss) so với lớp lớn nhất.
    #    Chúng ta muốn tối đa hóa tỷ lệ của lớp thiểu số.
    results_df['balance_score'] = results_df[['win_train', 'loss_train']].min(axis=1) / results_df[['win_train', 'loss_train']].max(axis=1)

    # 2. Phạt Timeout (Timeout Penalty): Gần 1 là tốt nhất.
    #    Bị phạt mạnh khi timeout > 50%, nhưng timeout cũng k nên quá thấp (< 15%)
    results_df['actionability_score'] = 1 - results_df['timeout_train']
    # Phạt nặng hơn
    results_df.loc[results_df['timeout_train'] > 0.5, 'actionability_score'] *= 0.4 
    results_df.loc[results_df['timeout_train'] < 0.2, 'actionability_score'] *= 0.55

    # 3. Phạt Bất ổn định (Stability Penalty): Gần 1 là tốt nhất.
    #    Đo chênh lệch tương đối giữa train và test.
    win_diff = abs(results_df['win_test'] - results_df['win_train']) / (results_df['win_train'] + 1e-9)
    loss_diff = abs(results_df['loss_test'] - results_df['loss_train']) / (results_df['loss_train'] + 1e-9)
    results_df['stability_score'] = 1 - (win_diff + loss_diff) / 2
    # Giới hạn điểm phạt, không để nó âm
    results_df['stability_score'] = results_df['stability_score'].clip(lower=0)
    
    # 4. Thưởng Risk/Reward (RR Bonus)
    rr = results_df['tp_pct'] / results_df['sl_pct']
    # Chuẩn hóa về thang điểm [0, 1]. Giả sử R/R hợp lý nằm trong khoảng [1, 3]
    min_rr, max_rr = 1.0, 2.5
    results_df['rr_score'] = (rr.clip(lower=min_rr, upper=max_rr) - min_rr) / (max_rr - min_rr)

    # 5. Điểm số Horizon (Horizon Score) - Ưu tiên horizon lớn hơn
    # Sử dụng một hàm tuyến tính hoặc log để chuẩn hóa horizon về thang điểm [0, 1]
    results_df['horizon_score'] = results_df['h'].apply(lambda x: 1 if x in [10, 15] else 1 - (max(10 - x, x - 15))/10).clip(lower=0)
    
    # --- TÍNH ĐIỂM CUỐI CÙNG (CÓ TRỌNG SỐ) ---
    weights = {
        'balance': 0.35,
        'actionability': 0.35,
        'stability': 0.1,
        'horizon': 0.1,
        'rr': 0.1
    }
    results_df['final_score'] = (
        results_df['balance_score'] * weights['balance'] +
        results_df['actionability_score'] * weights['actionability'] +
        results_df['stability_score'] * weights['stability'] +
        results_df['horizon_score'] * weights['horizon'] +
        results_df['rr_score'] * weights['rr']
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
    return best_params, results_df
    
class TripleBarrierTask(ForecastingTask):
    def __init__(self, task_id: str,
                 horizon: int = 10,
                 tp_pct: float = 0.05,
                 sl_pct: float = 0.03,
                 require_cdl_features: int = 7,
                 require_non_cdl_features: int = 45):
        super().__init__(task_id, 'clf', 'category', require_cdl_features, require_non_cdl_features)
        self.horizon = horizon
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        
        self.targets = [f'target_tb_{horizon}d_{tp_pct*100:.0f}tp_{sl_pct*100:.0f}sl']
        self.target_for_selection = self.targets[0]
        
    def get_metadata(self):
        _super_metadata = super().get_metadata()
        _super_metadata['horizon'] = self.horizon
        _super_metadata['tp_pct'] = self.tp_pct
        _super_metadata['sl_pct'] = self.sl_pct
        
        return _super_metadata
    
    def load_metadata(self, task_meta):
        super().load_metadata(task_meta)
        self.horizon = int(task_meta['horizon'])
        self.tp_pct = float(task_meta['tp_pct'])
        self.sl_pct = float(task_meta['sl_pct'])
        
    
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        if 'ticker' not in df.columns:
            raise ValueError("DataFrame must have a 'ticker' column for group-aware target creation.")
            
        all_labels = []
        for _, group in df.groupby('ticker'):
            labels = get_triple_barrier_labels(group[base_price_col], self.horizon, self.tp_pct, self.sl_pct)
            all_labels.append(labels)
        
        return pd.concat(all_labels).to_frame(name=self.targets[0])