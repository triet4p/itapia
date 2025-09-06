"""N-days distribution forecasting task implementation."""

import pandas as pd
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from ._task import ForecastingTask

from itapia_common.schemas.entities.analysis.forecasting import NDaysDistributionTaskMetadata

DISTRIBUTION_FEATURES = ['mean', 'std', 'min', 'max', 'q25', 'q75']


def create_distribution_targets(prices: pd.Series, horizon: int) -> pd.DataFrame:
    """Create distribution targets for price forecasting.
    
    Args:
        prices (pd.Series): Price series data
        horizon (int): Forecast horizon in days
        
    Returns:
        pd.DataFrame: DataFrame with distribution targets (mean, std, min, max, q25, q75)
    """
    targets = pd.DataFrame(index=prices.index)
    price_vals = prices.values
    
    # Create a 2D view of all possible future windows
    # Example: [[p1,p2,p3], [p2,p3,p4], [p3,p4,p5], ...]
    future_windows = sliding_window_view(price_vals, window_shape=horizon)
    
    # Our data consists of windows STARTING from tomorrow
    # So we need to shift the calculation results by 1 step
    
    num_predictions = len(price_vals) - horizon
    
    if num_predictions <= 0:
        return targets  # Not enough data
        
    # Get future windows for each point (from t+1 to t+horizon)
    # Window for day 0 is from day 1 to day horizon
    # Window for the last possible forecast day is from...
    windows_for_prediction = future_windows[1 : num_predictions + 1]
    
    # Calculate across all windows at once
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
    """N-days distribution forecasting task.
    
    This task creates targets based on the distribution of prices over a future horizon.
    """
    
    def __init__(self, task_id: str,
                 horizon: int = 5,
                 require_cdl_features: int = 7,
                 require_non_cdl_features: int = 45):
        """Initialize N-days distribution task.
        
        Args:
            task_id (str): Unique identifier for the task
            horizon (int, optional): Forecast horizon in days. Defaults to 5
            require_cdl_features (int, optional): Number of candle pattern features required. Defaults to 7
            require_non_cdl_features (int, optional): Number of non-candle pattern features required. Defaults to 45
        """
        super().__init__(task_id, 'reg', 'percent', require_cdl_features, require_non_cdl_features)
        self.horizon = horizon
        
        self.targets = [f'target_{s}_pct_{horizon}d' for s in DISTRIBUTION_FEATURES]
        self.target_for_selection = f'target_mean_pct_{horizon}d'
        
    def get_metadata(self):
        """Get metadata for the N-days distribution task.
        
        Returns:
            dict: Task metadata including horizon information
        """
        _super_metadata = super().get_metadata()
        _super_metadata['horizon'] = self.horizon
        
        return _super_metadata
    
    def get_metadata_for_plain(self) -> NDaysDistributionTaskMetadata:
        """Get plain metadata for the N-days distribution task.
        
        Returns:
            NDaysDistributionTaskMetadata: N-days distribution task metadata schema
        """
        return NDaysDistributionTaskMetadata(
            targets=self.targets,
            units=self.target_units,
            horizon=self.horizon
        )
    
    def load_metadata(self, task_meta):
        """Load metadata into the N-days distribution task.
        
        Args:
            task_meta (dict): Metadata dictionary to load
        """
        super().load_metadata(task_meta)
        self.horizon = int(task_meta['horizon'])
    
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        """Create N-days distribution targets for the DataFrame.
        
        Args:
            df (pd.DataFrame): Input DataFrame with price data
            base_price_col (str): Column name for base price data
            
        Returns:
            pd.DataFrame: DataFrame with normalized distribution targets
            
        Raises:
            KeyError: If DataFrame does not have a 'ticker' column
        """
        if 'ticker' not in df.columns:
            raise KeyError("DataFrame must have a 'ticker' column for group-aware target creation.")

        all_targets = []
        for _, group in df.groupby('ticker'):
            prices = group[base_price_col]
            
            # 1. Calculate absolute targets as before
            abs_targets = create_distribution_targets(prices, self.horizon)
            
            # 2. NORMALIZE
            # Get current closing price to use as denominator
            current_close = prices
            
            # Create new DataFrame to hold normalized targets
            norm_targets = pd.DataFrame(index=abs_targets.index)
            
            # Normalize mean, min, max, q25, q75 to percentage changes
            for stat in ['mean', 'min', 'max', 'q25', 'q75']:
                col_name = f'target_{stat}_{self.horizon}d'
                norm_targets[f'target_{stat}_pct_{self.horizon}d'] = \
                    ((abs_targets[col_name] - current_close) / current_close) * 100
            
            # Normalize std to percentage of current price
            col_std = f'target_std_{self.horizon}d'
            norm_targets[f'target_std_pct_{self.horizon}d'] = \
                (abs_targets[col_std] / current_close) * 100

            all_targets.append(norm_targets)
        
        return pd.concat(all_targets)