# forecasting/task.py

import pandas as pd

from abc import ABC, abstractmethod
from typing import Literal, Dict, List

from itapia_common.dblib.schemas.reports.forecasting import _BaseTaskMetadata

import app.core.config as cfg

class ForecastingTask(ABC):
    def __init__(self, task_id: str, task_type: Literal['clf', 'reg'],
                 target_units: Literal['percent', 'category'],
                 require_cdl_features: int = 7,
                 require_non_cdl_features: int = 45):
        self.task_id = task_id
        self.task_type = task_type
        
        self.targets: List[str] = []
        self.selected_features: List[str] = []
        self.non_cdl_features_cnt: int = require_non_cdl_features
        self.cdl_features_cnt: int = require_cdl_features
        
        self.target_for_selection: str = ""
        
        self.target_units: Literal['percent', 'category'] = target_units
        
    def get_metadata(self) -> Dict:
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
        pass
        
    def load_metadata(self, task_meta: dict):
        """
        Khôi phục trạng thái của Task từ một dictionary metadata.
        
        Args:
            task_meta (dict): Dictionary chứa metadata của task,
                              thường được trích xuất từ file metadata.json.
        """
        print(f"  - Loading metadata into task '{self.task_id}'...")
        
        # Khôi phục các thuộc tính cơ bản
        self.targets = task_meta.get('targets', [])
        self.target_for_selection = task_meta.get('target_for_selection', '')
        
        # Khôi phục thông tin về features
        features_meta = task_meta.get('features', {})
        self.selected_features = features_meta.get('details', [])
        self.non_cdl_features_cnt = features_meta.get('non_cdl_features_cnt', self.non_cdl_features_cnt)
        self.cdl_features_cnt = features_meta.get('cdl_features_cnt', self.cdl_features_cnt)
        
        print("  - Task metadata loaded successfully.")
    
    def __eq__(self, value):
        if not isinstance(value, ForecastingTask):
            return False
        return value.task_id == self.task_id
    
    def __hash__(self):
        return hash(self.task_id)
    
    @abstractmethod
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        pass