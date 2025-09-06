"""Triple barrier forecasting task implementation."""

import pandas as pd
import numpy as np
from ._task import ForecastingTask
from itapia_common.schemas.entities.analysis.forecasting import TripleBarrierTaskMetadata


def get_triple_barrier_labels(prices: pd.Series, h: int, tp_pct: float, sl_pct: float) -> pd.Series:
    """Assign labels based on the Triple-Barrier method (Improved version).
    
    Initialize labels as NaN to clearly distinguish points that cannot be labeled
    (due to insufficient future data) from points with label 0 (timeout).
    
    Args:
        prices (pd.Series): Price series data
        h (int): Horizon in days
        tp_pct (float): Take-profit percentage threshold
        sl_pct (float): Stop-loss percentage threshold
        
    Returns:
        pd.Series: Series with labels (1 for win, -1 for loss, 0 for timeout, NaN for insufficient data)
    """
    # Initialize label series with NaN instead of 0
    out = pd.Series(index=prices.index, data=np.nan, dtype=np.float16)

    # Calculate barriers for each time point
    upper_barrier = prices * (1 + tp_pct)
    lower_barrier = prices * (1 - sl_pct)

    # Loop only runs to the point where we have enough h days in the future
    for i in range(len(prices) - h):
        future_window = prices.iloc[i + 1 : i + 1 + h]
        
        hit_tp = future_window[future_window >= upper_barrier.iloc[i]]
        hit_sl = future_window[future_window <= lower_barrier.iloc[i]]

        first_tp_time = hit_tp.index.min() if not hit_tp.empty else pd.NaT
        first_sl_time = hit_sl.index.min() if not hit_sl.empty else pd.NaT

        if pd.isna(first_tp_time) and pd.isna(first_sl_time):
            # No barrier hit -> Timeout
            out.iloc[i] = 0
        elif pd.isna(first_sl_time) or first_tp_time < first_sl_time:
            # Upper barrier hit first -> Win
            out.iloc[i] = 1
        else:
            # Lower barrier hit first -> Loss
            out.iloc[i] = -1
            
    # At this step, the last h rows of `out` will be NaN.
    # We can decide how to handle them.
    # The best choice is to remove them along with corresponding features
    # before training the model.
    
    # This function only returns a series containing NaN.
    # Removing NaN will be done in the next step.
    return out


def generate_adaptive_grid(atr_percent):
    """Generate an adaptive parameter grid based on average true range percentage.
    
    Args:
        atr_percent (float): Average true range percentage (daily volatility)
        
    Returns:
        dict: Dictionary with horizons, take-profit percentages, and stop-loss percentages
    """
    # atr_percent is the average daily volatility
    # A reasonable target could be 3 to 10 times the daily volatility
    
    # tp_pcts will be multiples of atr_percent
    tp_multipliers = [3, 5, 8, 12] 
    tp_pcts = [round(atr_percent * m, 3) for m in tp_multipliers]

    # sl_pcts will be a fraction of tp_pcts
    sl_ratios = [0.5, 0.67] 
    sl_pcts = []
    for tp in tp_pcts:
        for ratio in sl_ratios:
            sl_pcts.append(round(tp * ratio, 3))
    
    # Remove duplicates and sort
    tp_pcts = sorted(list(set(tp_pcts)))
    sl_pcts = sorted(list(set(sl_pcts)))

    # horizons can remain the same
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
    """Automatically find optimal Triple Barrier parameters by running grid search
    and scoring results based on defined criteria.
    
    Args:
        df_train (pd.DataFrame): Training DataFrame
        df_test (pd.DataFrame): Test DataFrame (recent data)
        base_price_col (str): Column name for base price data
        horizons (list): List of horizon values to search
        tp_pcts (list): List of take-profit percentages to search
        sl_pcts (list): List of stop-loss percentages to search
        
    Returns:
        dict: Dictionary containing the best parameters ('h', 'tp_pct', 'sl_pct')
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

                # Label both datasets
                # --- FIX: Apply get_triple_barrier_labels to each ticker group ---
                train_labels_list = [get_triple_barrier_labels(group[base_price_col], h, tp, sl) for _, group in df_train.groupby('ticker')]
                train_labels = pd.concat(train_labels_list).dropna()

                test_labels_list = [get_triple_barrier_labels(group[base_price_col], h, tp, sl) for _, group in df_test.groupby('ticker')]
                test_labels = pd.concat(test_labels_list).dropna()
                # --- END FIX ---
                
                if train_labels.empty or test_labels.empty: continue

                # Calculate distribution
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

    # --- SCORING FUNCTION ---
    # 1. Balance Score: Closer to 1 is better.
    #    Use the ratio of the minority class (win, loss) to the majority class.
    #    We want to maximize the ratio of the minority class.
    results_df['balance_score'] = results_df[['win_train', 'loss_train']].min(axis=1) / results_df[['win_train', 'loss_train']].max(axis=1)

    # 2. Timeout Penalty: Closer to 1 is better.
    #    Heavily penalized when timeout > 50%, but timeout shouldn't be too low (< 15%)
    results_df['actionability_score'] = 1 - results_df['timeout_train']
    # Heavier penalty
    results_df.loc[results_df['timeout_train'] > 0.5, 'actionability_score'] *= 0.4 
    results_df.loc[results_df['timeout_train'] < 0.2, 'actionability_score'] *= 0.55

    # 3. Stability Penalty: Closer to 1 is better.
    #    Measure relative difference between train and test.
    win_diff = abs(results_df['win_test'] - results_df['win_train']) / (results_df['win_train'] + 1e-9)
    loss_diff = abs(results_df['loss_test'] - results_df['loss_train']) / (results_df['loss_train'] + 1e-9)
    results_df['stability_score'] = 1 - (win_diff + loss_diff) / 2
    # Limit penalty score, don't let it go negative
    results_df['stability_score'] = results_df['stability_score'].clip(lower=0)
    
    # 4. Risk/Reward Bonus
    rr = results_df['tp_pct'] / results_df['sl_pct']
    # Normalize to [0, 1] scale. Assume reasonable R/R is in range [1, 3]
    min_rr, max_rr = 1.0, 2.5
    results_df['rr_score'] = (rr.clip(lower=min_rr, upper=max_rr) - min_rr) / (max_rr - min_rr)

    # 5. Horizon Score - Prefer larger horizons
    # Use a linear or log function to normalize horizon to [0, 1] scale
    results_df['horizon_score'] = results_df['h'].apply(lambda x: 1 if x in [10, 15] else 1 - (max(10 - x, x - 15))/10).clip(lower=0)
    
    # --- CALCULATE FINAL SCORE (WEIGHTED) ---
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
    
    # Sort and view top candidates
    sorted_results = results_df.sort_values(by='final_score', ascending=False)
    print("\nTop 5 candidates based on automated scoring:")
    print(sorted_results.head(5)[['h', 'tp_pct', 'sl_pct', 'final_score', 'balance_score', 'actionability_score', 'stability_score']])
    
    # Get the best parameters
    best_params_row = sorted_results.iloc[0]
    best_params = {
        'h': int(best_params_row['h']),
        'tp_pct': best_params_row['tp_pct'],
        'sl_pct': best_params_row['sl_pct']
    }
    
    print(f"\n==> Automatically selected best parameters: {best_params}")
    return best_params, results_df
    

class TripleBarrierTask(ForecastingTask):
    """Triple barrier forecasting task.
    
    This task creates targets based on the triple barrier method for labeling.
    """
    
    def __init__(self, task_id: str,
                 horizon: int = 10,
                 tp_pct: float = 0.05,
                 sl_pct: float = 0.03,
                 require_cdl_features: int = 7,
                 require_non_cdl_features: int = 45):
        """Initialize triple barrier task.
        
        Args:
            task_id (str): Unique identifier for the task
            horizon (int, optional): Forecast horizon in days. Defaults to 10
            tp_pct (float, optional): Take-profit percentage. Defaults to 0.05
            sl_pct (float, optional): Stop-loss percentage. Defaults to 0.03
            require_cdl_features (int, optional): Number of candle pattern features required. Defaults to 7
            require_non_cdl_features (int, optional): Number of non-candle pattern features required. Defaults to 45
        """
        super().__init__(task_id, 'clf', 'category', require_cdl_features, require_non_cdl_features)
        self.horizon = horizon
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        
        self.targets = [f'target_tb_{horizon}d_{tp_pct*100:.0f}tp_{sl_pct*100:.0f}sl']
        self.target_for_selection = self.targets[0]
        
    def get_metadata(self):
        """Get metadata for the triple barrier task.
        
        Returns:
            dict: Task metadata including horizon, take-profit, and stop-loss information
        """
        _super_metadata = super().get_metadata()
        _super_metadata['horizon'] = self.horizon
        _super_metadata['tp_pct'] = self.tp_pct
        _super_metadata['sl_pct'] = self.sl_pct
        
        return _super_metadata
    
    def get_metadata_for_plain(self) -> TripleBarrierTaskMetadata:
        """Get plain metadata for the triple barrier task.
        
        Returns:
            TripleBarrierTaskMetadata: Triple barrier task metadata schema
        """
        return TripleBarrierTaskMetadata(
            targets=self.targets,
            units=self.target_units,
            horizon=self.horizon,
            tp_pct=self.tp_pct,
            sl_pct=self.sl_pct
        )
    
    def load_metadata(self, task_meta):
        """Load metadata into the triple barrier task.
        
        Args:
            task_meta (dict): Metadata dictionary to load
        """
        super().load_metadata(task_meta)
        self.horizon = int(task_meta['horizon'])
        self.tp_pct = float(task_meta['tp_pct'])
        self.sl_pct = float(task_meta['sl_pct'])
        
    
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        """Create triple barrier targets for the DataFrame.
        
        Args:
            df (pd.DataFrame): Input DataFrame with price data
            base_price_col (str): Column name for base price data
            
        Returns:
            pd.DataFrame: DataFrame with triple barrier labels
            
        Raises:
            ValueError: If DataFrame does not have a 'ticker' column
        """
        if 'ticker' not in df.columns:
            raise ValueError("DataFrame must have a 'ticker' column for group-aware target creation.")
            
        all_labels = []
        for _, group in df.groupby('ticker'):
            labels = get_triple_barrier_labels(group[base_price_col], self.horizon, self.tp_pct, self.sl_pct)
            all_labels.append(labels)
        
        return pd.concat(all_labels).to_frame(name=self.targets[0])