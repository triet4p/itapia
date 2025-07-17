from app.forecasting.training.feature_selection import *
from app.forecasting.training.data_split import *

from app.forecasting.task import _MLTask

from app.logger import *

from typing import List, Dict

class TrainingOrchestrator:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.tasks: Dict[str, _MLTask] = {}
        self.feature_cols = [c for c in df.columns if not c.startswith('target_')]
        self.feature_cols.remove('ticker')
        
    def register_task(self, new_task: _MLTask):
        info(f'Training Orchestrator: Registering problem: {new_task.task_id} ({new_task.task_type})')
        self.tasks[new_task.task_id] = new_task
        
    def _run_feature_selection_each_task(self, task: _MLTask,
                                         weights: Dict,
                                         bonus_features: List[str],
                                         bonus_multiplier: float):
        info(f'Training Orchestrator: Create target for task {task.task_id}')
        
        targets = task.create_targets(self.df, base_price_col='close')
        target_for_fs = targets[task.target_for_selection]
        
        valid_indices = target_for_fs.dropna().index
        X_fs = self.df.loc[valid_indices, self.feature_cols]
        y_fs = target_for_fs.loc[valid_indices]
        
        info(f'Training Orchestrator: Ranking features for {task.task_id}')
        ranks_df = get_ensemble_feature_ranks(X_fs, y_fs, task_type=task.task_type)
        ranks_df = get_ranked_features(ranks_df, weights, bonus_features, bonus_multiplier)
        
        info(f'Training Orchestrator: Select {task.non_cdl_features_cnt} non cdl features and {task.cdl_features_cnt} cdl features for {task.task_id}')
        selected = select_k_plus_l_features(ranks_df, task.non_cdl_features_cnt, task.cdl_features_cnt)
        
        task.selected_features = selected
        
    def run_feature_selection(self,
                              weights: Dict,
                              bonus_features: List[str] = [],
                              bonus_multiplier: float = 1.0):
        info(f'Training Orchestrator: Running feature selection for all tasks ...')
        for task_id, task in self.tasks.items():
            self._run_feature_selection_each_task(task,
                                                  weights,
                                                  bonus_features, 
                                                  bonus_multiplier)
            
    

        
    