from sklearn.metrics import f1_score, root_mean_squared_error
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
        
        self._train_df: pd.DataFrame = None
        self._test_df: pd.DataFrame = None
        
    def register_task(self, new_task: _MLTask):
        info(f'Training Orchestrator: Registering problem: {new_task.task_id} ({new_task.task_type})')
        self.tasks[new_task.task_id] = new_task
    
    def _create_target_each_task(self, task: _MLTask):
        info(f'Training Orchestrator: Create target for task {task.task_id}')
        
        targets = task.create_targets(self.df, base_price_col='close')
        return targets
        
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
        
        return selected
        
    def create_targets(self):
        info(f'Training Orchestrator: Running target creation for all tasks ...')
        all_targets = []
        for task_id, task in self.tasks.items():
            targets = self._create_target_each_task(task)
            all_targets.append(targets)
            
        self.df = pd.concat([self.df] + all_targets, axis=1)
            
        
    def select_features(self, weights: Dict,
                        bonus_features: List[str] = [],
                        bonus_multiplier: float = 1.0):
        info(f'Training Orchestrator: Running feature selection for all tasks ...')
        for task_id, task in self.tasks.items():
            task.selected_features = self._run_feature_selection_each_task(task,
                                                  weights,
                                                  bonus_features, 
                                                  bonus_multiplier)
            
    def split_train_test(self,
                         train_test_split_date: datetime,
                         test_last_date: datetime = datetime.now()):
        self._train_df, self._test_df = train_test_split(self.df, train_test_split_date, test_last_date)
    
    def _walk_forward_validate_each_task(self, task: _MLTask, 
                                         model_class, model_params, model_name,
                                         validation_months: int = 3):
        evaluation_results = []
        model_snapshots = {}
        
        task.set_model(model_class, model_params, model_name)
        
        generator = get_walk_forward_splits(self._train_df,
                                            validation_months)
        
        for i, (train_df, valid_df) in enumerate(generator):
            X_train, y_train = train_df[task.selected_features], train_df[task.targets]
            X_valid, y_valid = valid_df[task.selected_features], valid_df[task.targets]
            print(y_train.shape)
            
            snapshot_model = model_class(**task.model_params)
            snapshot_model.fit(X_train, y_train)
            
            model_snapshots[f'model_fold_{i+1}.pkl'] = snapshot_model
            
            preds = snapshot_model.predict(X_valid)
            if task.task_type == 'clf':
                score = f1_score(y_valid, preds, average='micro')
                metric_name = 'f1_micro'
            else:
                score = root_mean_squared_error(y_valid, preds, squared=False)
                metric_name = 'rmse'
                
            evaluation_results.append({'fold': i+1, metric_name: score})
            print(f"  - Fold {i+1} | Validation Metric ({metric_name}): {score:.4f}")
        
        return evaluation_results, model_snapshots
    
    def walk_forward_validate(self, 
                              model_class, model_params, model_name,
                              validation_months: int = 3):
        for task_id, task in self.tasks.items():
            evaluation_results, model_snapshots = self._walk_forward_validate_each_task(
                task, model_class, model_params, model_name, validation_months
            )
            task.model_snapshots = model_snapshots
            task.extra_artifacts['walk_forward_evaluation_details'] = pd.DataFrame(evaluation_results)
            
    def _finalize_train_each_task(self, task: _MLTask):
        X_final, y_final = self._train_df[task.selected_features], self._train_df[task.targets]
        task.model.fit(X_final, y_final)
        
    def finalize_train(self):
        for task_id, task in self.tasks.items():
            self._finalize_train_each_task(task)            