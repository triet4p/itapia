"""Base module for forecasting tasks."""

import pandas as pd

from abc import ABC, abstractmethod
from typing import Literal, Dict, List

from itapia_common.schemas.entities.analysis.forecasting import _BaseTaskMetadata


class ForecastingTask(ABC):
    """A base class for a Forecasting Task (a problem that a forecasting model needs to solve)."""
    
    def __init__(self, task_id: str, task_type: Literal['clf', 'reg'],
                 target_units: Literal['percent', 'category'],
                 require_cdl_features: int = 7,
                 require_non_cdl_features: int = 45):
        """Initialize a Forecasting Task.
        
        Args:
            task_id (str): ID of task
            task_type (Literal['clf', 'reg']): Type of task, 'clf' for classification and 'reg' for regression
            target_units (Literal['percent', 'category']): Units of targets, 'percent' for % and 'category' for classification label output
            require_cdl_features (int, optional): Number of candle pattern features required. Defaults to 7
            require_non_cdl_features (int, optional): Number of non-candle pattern features required. Defaults to 45
        """
        self.task_id = task_id
        self.task_type = task_type
        
        self.targets: List[str] = []
        self.selected_features: List[str] = []
        self.non_cdl_features_cnt: int = require_non_cdl_features
        self.cdl_features_cnt: int = require_cdl_features
        
        self.target_for_selection: str = ""
        
        self.target_units: Literal['percent', 'category'] = target_units
        
    def get_metadata(self) -> Dict:
        """Get metadata for the forecasting task.
        
        Returns:
            Dict: Dictionary containing task metadata including ID, type, targets, and features
        """
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "targets": self.targets,
            "target_units": self.target_units,
            "target_for_selection": self.target_for_selection,
            "features": {
                "num_selected": len(self.selected_features),
                "cdl_features_cnt": self.cdl_features_cnt,
                "non_cdl_features_cnt": self.non_cdl_features_cnt,
                'details': self.selected_features
            }
        }
        
    def get_metadata_for_plain(self) -> _BaseTaskMetadata:
        """Get plain metadata for the forecasting task.
        
        Returns:
            _BaseTaskMetadata: Base task metadata schema
        """
        pass
        
    def load_metadata(self, task_meta: dict):
        """Load metadata into the task.
        
        Args:
            task_meta (dict): Metadata dictionary to load
        """
        print(f"  - Loading metadata into task '{self.task_id}'...")
        
        self.targets = task_meta.get('targets', [])
        self.target_for_selection = task_meta.get('target_for_selection', '')
        
        features_meta = task_meta.get('features', {})
        self.selected_features = features_meta.get('details', [])
        self.non_cdl_features_cnt = features_meta.get('non_cdl_features_cnt', self.non_cdl_features_cnt)
        self.cdl_features_cnt = features_meta.get('cdl_features_cnt', self.cdl_features_cnt)
        
        print("  - Task metadata loaded successfully.")
    
    def __eq__(self, value):
        """Check equality based on task ID.
        
        Args:
            value: Object to compare with
            
        Returns:
            bool: True if objects are equal, False otherwise
        """
        if not isinstance(value, ForecastingTask):
            return False
        return value.task_id == self.task_id
    
    def __hash__(self):
        """Get hash based on task ID.
        
        Returns:
            int: Hash of the task ID
        """
        return hash(self.task_id)
    
    @abstractmethod
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        """Create target values for the forecasting task.
        
        Args:
            df (pd.DataFrame): Input DataFrame with price data
            base_price_col (str): Column name for base price data
            
        Returns:
            pd.DataFrame: DataFrame with target values
        """
        pass