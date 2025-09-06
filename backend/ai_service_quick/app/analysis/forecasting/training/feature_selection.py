"""Feature selection utilities for forecasting model training."""

from typing import Literal, List, Dict
from lightgbm import LGBMClassifier, LGBMRegressor
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression


def get_ensemble_feature_ranks(X: pd.DataFrame, y: pd.Series, task_type: Literal['clf', 'reg']) -> pd.DataFrame:
    """Rank features using multiple methods and ensemble the results.
    
    Args:
        X (pd.DataFrame): DataFrame containing features
        y (pd.Series): Series containing target variable
        task_type (Literal['clf', 'reg']): 'clf' for classification or 'reg' for regression
        
    Returns:
        pd.DataFrame: DataFrame containing scores and ranks from each method
    """
    ranks = pd.DataFrame(index=X.columns)
    
    # --- Method 1: RandomForest Importance (Gini Importance) ---
    print("Ranking with RandomForest...")
    if task_type == 'clf':
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    else:
        rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    ranks['rf_score'] = rf.feature_importances_
    ranks['rf_rank'] = ranks['rf_score'].rank(method='first', ascending=False)
    
    # --- Method 2: LightGBM Importance (Split/Gain) ---
    print("Ranking with LightGBM...")
    if task_type == 'clf':
        lgb = LGBMClassifier(random_state=42, n_jobs=-1, verbose=-1)
    else:
        lgb = LGBMRegressor(random_state=42, n_jobs=-1, verbose=-1)
    lgb.fit(X, y)
    ranks['lgbm_score'] = lgb.feature_importances_
    ranks['lgbm_rank'] = ranks['lgbm_score'].rank(method='first', ascending=False)

    # --- Method 3: Mutual Information ---
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
    """Calculate final scores from raw ranking table.
    
    Args:
        ranks_df (pd.DataFrame): DataFrame with raw rankings
        weights (Dict): Dictionary of weights for each ranking method
        bonus_features (List[str], optional): List of features to apply bonus multiplier. Defaults to []
        bonus_multiplier (float, optional): Multiplier for bonus features. Defaults to 1.0
        
    Returns:
        pd.DataFrame: DataFrame sorted by final scores
    """
    # Normalize scores
    score_cols = [col for col in ranks_df.columns if col.endswith('_score')]
    for col in score_cols:
        min_val, max_val = ranks_df[col].min(), ranks_df[col].max()
        ranks_df[f'{col}_norm'] = (ranks_df[col] - min_val) / (max_val - min_val) if max_val > min_val else 0.5
    
    # Calculate weighted score
    norm_score_cols = [f'{col}_norm' for col in score_cols]
    ranks_df['final_score_raw'] = np.average(ranks_df[norm_score_cols], axis=1, weights=[weights[sc.split('_')[0]] for sc in score_cols])

    # Apply bonuses
    for feature in bonus_features:
        if feature in ranks_df.index:
            ranks_df.loc[feature, 'final_score_raw'] *= bonus_multiplier
            
    return ranks_df.sort_values(by='final_score_raw', ascending=False)


def select_k_plus_l_features(ranks_df: pd.DataFrame, k=45, l=5, cdl_prefix='CDL_') -> List[str]:
    """Select K best non-CDL features and L best CDL features.
    
    Args:
        ranks_df (pd.DataFrame): Ranked DataFrame
        k (int, optional): Number of non-CDL features to select. Defaults to 45
        l (int, optional): Number of CDL features to select. Defaults to 5
        cdl_prefix (str, optional): Prefix for candlestick pattern columns. Defaults to 'CDL_'
        
    Returns:
        List[str]: List of selected feature names
    """
    # Split into two groups
    cdl_features_ranked = ranks_df[ranks_df.index.str.startswith(cdl_prefix)]
    non_cdl_features_ranked = ranks_df[~ranks_df.index.str.startswith(cdl_prefix)]
    
    # Get top K and top L
    top_k_non_cdl = non_cdl_features_ranked.head(k).index.tolist()
    top_l_cdl = cdl_features_ranked.head(l).index.tolist()
    
    # Combine
    final_features = top_k_non_cdl + top_l_cdl
    
    print(f"Selected {len(top_k_non_cdl)} top non-candlestick features.")
    print(f"Selected {len(top_l_cdl)} top candlestick features.")
    print(f"Total features: {len(final_features)}")
    
    return final_features