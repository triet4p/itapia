from app.forecasting.training.feature_selection import *
from app.forecasting.training.data_split import *

from app.forecasting.task import _MLTask

from app.logger import *

from typing import List, Dict

class TrainingOrchestrator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.tasks: Dict[str, _MLTask] = {}
        self.feature_cols = [c for c in df.columns if not c.startswith('target_')]
        self.feature_cols.remove('ticker')
        
    def register_task(self, new_task: _MLTask):
        info(f'Training Orchestrator: Registering problem: {new_task.task_id} ({new_task.task_type})')
        self.tasks[new_task.task_id] = new_task
    
    def _create_target_each_task(self, task: _MLTask):
        info(f'Training Orchestrator: Create target for task {task.task_id}')
        
        targets = task.create_targets(self.df, base_price_col='close')
        self.df = pd.concat([self.df, targets], axis=1)
        
    def _run_feature_selection_each_task(self, task: _MLTask,
                                         weights: Dict,
                                         bonus_features: List[str],
                                         bonus_multiplier: float):
        info(f'Training Orchestrator: Selection features for {task.task_id}')
        target_col = task.target_for_selection
        temp_df = self.df.dropna(subset=[target_col])
        temp_df.drop(columns='ticker', inplace=True)
        X_fs = temp_df[self.feature_cols]
        y_fs = temp_df[target_col]
        
        info(f'Training Orchestrator: Ranking features for {task.task_id}')
        ranks_df = get_ensemble_feature_ranks(X_fs, y_fs, task_type=task.task_type)
        ranks_df = get_ranked_features(ranks_df, weights, bonus_features, bonus_multiplier)
        
        info(f'Training Orchestrator: Select {task.non_cdl_features_cnt} non cdl features and {task.cdl_features_cnt} cdl features for {task.task_id}')
        selected = select_k_plus_l_features(ranks_df, task.non_cdl_features_cnt, task.cdl_features_cnt)
        
        task.selected_features = selected
        
    def prepare_feature(self,
                              weights: Dict,
                              bonus_features: List[str] = [],
                              bonus_multiplier: float = 1.0):
        info(f'Training Orchestrator: Running feature selection for all tasks ...')
        for task_id, task in self.tasks.items():
            self._create_target_each_task(task)
            self._run_feature_selection_each_task(task,
                                                  weights,
                                                  bonus_features, 
                                                  bonus_multiplier)
            
    

        
    