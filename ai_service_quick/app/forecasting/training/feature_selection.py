# forecasting/training/feature_selection.py
from typing import Literal, List, Dict
from lightgbm import LGBMClassifier, LGBMRegressor
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
def get_ensemble_feature_ranks(X: pd.DataFrame, y: pd.Series, task_type: Literal['clf', 'reg']):
    """
    Xếp hạng các đặc trưng bằng nhiều phương pháp và tổng hợp kết quả.
    
    Args:
        X (pd.DataFrame): DataFrame chứa các đặc trưng.
        y (pd.Series): Chuỗi chứa biến mục tiêu.
        task_type (str): 'classification' hoặc 'regression'.
        
    Returns:
        pd.DataFrame: Một DataFrame chứa điểm số và thứ hạng từ mỗi phương pháp.
    """
    ranks = pd.DataFrame(index=X.columns)
    
    # --- Phương pháp 1: RandomForest Importance (Gini Importance) ---
    print("Ranking with RandomForest...")
    if task_type == 'clf':
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    else:
        rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    ranks['rf_score'] = rf.feature_importances_
    ranks['rf_rank'] = ranks['rf_score'].rank(method='first', ascending=False)
    
    # --- Phương pháp 2: LightGBM Importance (Split/Gain) ---
    print("Ranking with LightGBM...")
    if task_type == 'clf':
        lgb = LGBMClassifier(random_state=42, n_jobs=-1)
    else:
        lgb = LGBMRegressor(random_state=42, n_jobs=-1)
    lgb.fit(X, y)
    ranks['lgbm_score'] = lgb.feature_importances_
    ranks['lgbm_rank'] = ranks['lgbm_score'].rank(method='first', ascending=False)

    # --- Phương pháp 3: Mutual Information ---
    print("Ranking with Mutual Information...")
    if task_type == 'clf':
        mi = mutual_info_classif(X, y, random_state=42)
    else:
        mi = mutual_info_regression(X, y, random_state=42)
    ranks['mi_score'] = mi
    ranks['mi_rank'] = ranks['mi_score'].rank(method='first', ascending=False)
    
    return ranks

def get_ranked_features(ranks_df: pd.DataFrame, weights: Dict, 
                        bonus_features: List[str] = [], bonus_multiplier: float = 1.0) -> pd.DataFrame:
    """Từ bảng rank thô, tính toán điểm số cuối cùng."""
    # Chuẩn hóa score
    score_cols = [col for col in ranks_df.columns if col.endswith('_score')]
    for col in score_cols:
        min_val, max_val = ranks_df[col].min(), ranks_df[col].max()
        ranks_df[f'{col}_norm'] = (ranks_df[col] - min_val) / (max_val - min_val) if max_val > min_val else 0.5
    
    # Tính score có trọng số
    norm_score_cols = [f'{col}_norm' for col in score_cols]
    ranks_df['final_score_raw'] = np.average(ranks_df[norm_score_cols], axis=1, weights=[weights[sc.split('_')[0]] for sc in score_cols])

    # Áp dụng bonus
    for feature in bonus_features:
        if feature in ranks_df.index:
            ranks_df.loc[feature, 'final_score_raw'] *= bonus_multiplier
            
    return ranks_df.sort_values(by='final_score_raw', ascending=False)

def select_k_plus_l_features(ranks_df: pd.DataFrame, k=45, l=5, cdl_prefix='CDL_'):
    """
    Chọn K đặc trưng số tốt nhất và L đặc trưng CDL tốt nhất.
    
    Args:
        ranks_df (pd.DataFrame): DataFrame đã được xếp hạng.
        k (int): Số lượng đặc trưng không phải CDL cần chọn.
        l (int): Số lượng đặc trưng CDL cần chọn.
        cdl_prefix (str): Tiền tố của các cột mẫu hình nến.
    """
    # Tách thành 2 nhóm
    cdl_features_ranked = ranks_df[ranks_df.index.str.startswith(cdl_prefix)]
    non_cdl_features_ranked = ranks_df[~ranks_df.index.str.startswith(cdl_prefix)]
    
    # Lấy top K và top L
    top_k_non_cdl = non_cdl_features_ranked.head(k).index.tolist()
    top_l_cdl = cdl_features_ranked.head(l).index.tolist()
    
    # Kết hợp lại
    final_features = top_k_non_cdl + top_l_cdl
    
    print(f"Selected {len(top_k_non_cdl)} top non-candlestick features.")
    print(f"Selected {len(top_l_cdl)} top candlestick features.")
    print(f"Total features: {len(final_features)}")
    
    return final_features