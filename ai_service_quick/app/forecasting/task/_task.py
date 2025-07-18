# forecasting/task.py

import pandas as pd

from abc import ABC, abstractmethod
from typing import Literal, Dict, List

import app.core.config as cfg

class ForecastingTask(ABC):
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
        
        self.metadata = None
        
    def get_metadata(self) -> Dict:
        self.metadata = {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "targets": self.targets,
            "target_for_selection": self.target_for_selection,\
            "features": {
                "num_selected": len(self.selected_features),
                "cdl_features_cnt": self.cdl_features_cnt,
                "non_cdl_features_cnt": self.non_cdl_features_cnt,
                'details': self.selected_features
            }
        }
        return self.metadata
    
    def __eq__(self, value):
        if not isinstance(value, ForecastingTask):
            return False
        return value.task_id == self.task_id
    
    def __hash__(self):
        return hash(self.task_id)
    
    @abstractmethod
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        pass