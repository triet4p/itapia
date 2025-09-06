"""Training orchestrator for forecasting models."""

import math
import pandas as pd
from datetime import datetime
from typing import Dict, List

from sklearn.metrics import f1_score, mean_squared_error

from app.analysis.forecasting.task import ForecastingTask
from app.analysis.forecasting.model import ForecastingModel
from .feature_selection import get_ensemble_feature_ranks, get_ranked_features, select_k_plus_l_features
from .data_split import get_walk_forward_splits, train_test_split

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('TrainingOrchestrator')


class TrainingOrchestrator:
    """Orchestrator for managing the complete forecasting model training pipeline."""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize Orchestrator with a DataFrame containing enriched features.
        
        The DataFrame is considered immutable.
        
        Args:
            df (pd.DataFrame): Input DataFrame with enriched features
        """
        self.raw_df = df.copy()  # Store original DF, immutable
        self.df_with_targets: pd.DataFrame = None  # Will be created later
        
        # Core structure: Manage (Model, Task) pairs
        # Key is task_id for easy access
        self.models_to_train: Dict[str, ForecastingModel] = {}
        
        self._train_df: pd.DataFrame = None
        self._test_df: pd.DataFrame = None
        
        self.feature_selected_tasks = set()
        
    def _create_id_for_orchestrate(self, model: ForecastingModel, task: ForecastingTask) -> str:
        """Create a unique identifier for model-task orchestration.
        
        Args:
            model (ForecastingModel): Model instance
            task (ForecastingTask): Task instance
            
        Returns:
            str: Unique identifier string
        """
        return f'{model.name}-for-{task.task_id}'
        
        
    def register_model_for_task(self, model: ForecastingModel, task: ForecastingTask):
        """Register a Model-Task pair. This is the main entry point.
        
        Args:
            model (ForecastingModel): Model to register
            task (ForecastingTask): Task to register
        """
        logger.info(f"Registering Model '{model.name}' for Task '{task.task_id}'")
        model.assign_task(task)
        self.models_to_train[self._create_id_for_orchestrate(model, task)] = model

    def prepare_all_targets(self):
        """Create targets for all registered tasks and generate a complete DataFrame."""
        logger.info("--- STEP 1: Preparing targets for all registered tasks ---")
        if not self.models_to_train:
            logger.warn("No models/tasks registered. Nothing to do.")
            return

        all_targets_list = []
        for model in self.models_to_train.values():
            targets = model.task.create_targets(self.raw_df, base_price_col='close')
            all_targets_list.append(targets)
            
        # Concatenate all targets to the original DF to create a complete DF
        self.df_with_targets = pd.concat([self.raw_df] + all_targets_list, axis=1)
        print(f"All targets created. New DataFrame shape: {self.df_with_targets.shape}")

    def run_feature_selection(self, weights: Dict, bonus_features: List[str], bonus_multiplier: float):
        """Run feature selection for all registered (Model, Task) pairs.
        
        Args:
            weights (Dict): Weights for different feature ranking methods
            bonus_features (List[str]): Features to apply bonus multiplier
            bonus_multiplier (float): Multiplier for bonus features
        """
        logger.info("--- STEP 2: Running feature selection for all tasks ---")
        feature_cols = [c for c in self.raw_df.columns if c != 'ticker']

        for id, model in self.models_to_train.items():
            logger.info(f"- Selecting features for task: {id}")
            task = model.task
            if task.task_id in self.feature_selected_tasks:
                logger.info('- This task has already run feature selection')
                continue
            
            target_col = task.target_for_selection
            temp_df = self.df_with_targets.dropna(subset=[target_col])
            
            X_fs = temp_df[feature_cols]
            y_fs = temp_df[target_col]
            
            ranks_df = get_ensemble_feature_ranks(X_fs, y_fs, task_type=task.task_type)
            ranked_df = get_ranked_features(ranks_df, weights, bonus_features, bonus_multiplier)
            
            selected = select_k_plus_l_features(ranked_df, task.non_cdl_features_cnt, task.cdl_features_cnt)
            
            # Assign selected features to Task (as it belongs to the problem definition)
            task.selected_features = selected
            self.feature_selected_tasks.add(task.task_id)

    def split_data(self, train_test_split_date: datetime, test_last_date: datetime = datetime.now()):
        """Split target-enriched data into train and test sets.
        
        Args:
            train_test_split_date (datetime): Date to split train and test sets
            test_last_date (datetime, optional): Last date for test set. Defaults to datetime.now()
        """
        logger.info("--- STEP 3: Splitting data into train and test sets ---")
        if self.df_with_targets is None:
            raise RuntimeError("Targets must be prepared before splitting data. Run `prepare_all_targets()` first.")
        self._train_df, self._test_df = train_test_split(self.df_with_targets, train_test_split_date, test_last_date)
        print(f"Train set shape: {self._train_df.shape}, Test set shape: {self._test_df.shape}")

    def run_walk_forward_validation(self, validation_months: int,
                                    max_train_months: int|None = None):
        """Run Walk-Forward Validation for all models.
        
        Args:
            validation_months (int): Number of months for validation in each fold
            max_train_months (int | None, optional): Maximum training months. Defaults to None
        """
        logger.info("--- STEP 4: Running Walk-Forward Validation ---")
        if self._train_df is None:
            raise RuntimeError("Data must be split before running validation. Run `split_data()` first.")

        for id, model in self.models_to_train.items():
            task = model.task
            logger.info(f"- Validating model for task: {id}")

            evaluation_results = []
            generator = get_walk_forward_splits(self._train_df, validation_months, 
                                                max_train_months=max_train_months)

            for i, (train_fold_df, valid_fold_df) in enumerate(generator):
                av_test_time = pd.to_datetime(valid_fold_df.index)[0].to_pydatetime()
                
                X_train = train_fold_df[task.selected_features]
                y_train_df = train_fold_df[task.targets]
                X_valid = valid_fold_df[task.selected_features]
                y_valid_df = valid_fold_df[task.targets]

                y_train = y_train_df.values.ravel() if task.task_type == 'clf' else y_train_df.values
                y_valid = y_valid_df.values.ravel() if task.task_type == 'clf' else y_valid_df.values

                snapshot_id = f'model-fold-{i+1}'
                model.register_snapshot(snapshot_id, available_test_time=av_test_time)
                model.fit(X_train, y_train, snapshot_id)
                
                preds = model.predict(X_valid, snapshot_id)
                if task.task_type == 'clf':
                    score = f1_score(y_valid, preds, average='weighted')
                    metric_name = 'f1_weighted'
                else:
                    score = math.sqrt(mean_squared_error(y_valid, preds, multioutput='uniform_average'))
                    metric_name = 'avg_rmse'
                
                evaluation_results.append({'fold': i+1, metric_name: score})

            # Assign results to model object
            model.metrics = evaluation_results
            print(f"  - Finished validation. Collected {len(model.snapshot_models)} snapshots.")

    def run_final_training_and_registration(self, kaggle_username: str):
        """Train final model on entire training set and register to Kaggle.
        
        Args:
            kaggle_username (str): Kaggle username for model registration
        """
        logger.info("--- STEP 5: Final Training and Registration ---")
        if self._train_df is None:
            raise RuntimeError("Data must be split before final training. Run `split_data()` first.")

        for task_id, model in self.models_to_train.items():
            task = model.task
            logger.info(f"- Finalizing model for task: {task_id}")
            
            X_final_train = self._train_df[task.selected_features]
            y_final_train_df = self._train_df[task.targets]
            y_final_train = y_final_train_df.values.ravel() if task.task_type == 'clf' else y_final_train_df.values
            
            X_final_test = self._test_df[task.selected_features]
            y_final_test_df = self._test_df[task.targets]
            y_final_test = y_final_test_df.values.ravel() if task.task_type == 'clf' else y_final_test_df.values
            
            model.fit(X_final_train, y_final_train)
            
            y_pred_test = model.predict(X_final_test)
            
            if task.task_type == 'clf':
                score = f1_score(y_final_test, y_pred_test, average='weighted')
                metric_name = 'f1_weighted'
            else:
                score = math.sqrt(mean_squared_error(y_final_test, y_pred_test, multioutput='uniform_average'))
                metric_name = 'avg_rmse'
                
            model.metrics.append({'fold': 'all', metric_name: score})
            
            # Instruct model to self-register
            model.register_model_to_kaggle(kaggle_username=kaggle_username)