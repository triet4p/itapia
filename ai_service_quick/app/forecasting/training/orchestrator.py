# forecasting/training/orchestrator.py

import math
import pandas as pd
from datetime import datetime
from typing import Dict, List

from sklearn.metrics import f1_score, mean_squared_error

from app.forecasting.task import ForecastingTask
from app.forecasting.model import ForecastingModel
from .feature_selection import get_ensemble_feature_ranks, get_ranked_features, select_k_plus_l_features
from .data_split import get_walk_forward_splits, train_test_split
from app.logger import info, warn
import app.core.config as cfg

class TrainingOrchestrator:
    def __init__(self, df: pd.DataFrame):
        """
        Khởi tạo Orchestrator với DataFrame chứa các đặc trưng đã làm giàu.
        DataFrame này được coi là bất biến.
        """
        self.raw_df = df.copy() # Lưu trữ DF gốc, bất biến
        self.df_with_targets: pd.DataFrame = None # Sẽ được tạo sau
        
        # Cấu trúc cốt lõi: Quản lý các cặp (Model, Task)
        # Key là task_id để dễ dàng truy cập
        self.models_to_train: Dict[str, ForecastingModel] = {}
        
        self._train_df: pd.DataFrame = None
        self._test_df: pd.DataFrame = None
        
        self.feature_selected_tasks = set()
        
    def _create_id_for_orchestrate(self, model: ForecastingModel, task: ForecastingTask):
        return f'{model.name}-for-{task.task_id}'
        
        
    def register_model_for_task(self, model: ForecastingModel, task: ForecastingTask):
        """
        Đăng ký một cặp Model và Task. Đây là điểm khởi đầu chính.
        """
        info(f"Registering Model '{model.name}' for Task '{task.task_id}'")
        model.assign_task(task)
        self.models_to_train[self._create_id_for_orchestrate(model, task)] = model

    def prepare_all_targets(self):
        """
        Tạo target cho tất cả các task đã đăng ký và tạo ra một DataFrame hoàn chỉnh.
        """
        info("--- STEP 1: Preparing targets for all registered tasks ---")
        if not self.models_to_train:
            warn("No models/tasks registered. Nothing to do.")
            return

        all_targets_list = []
        for model in self.models_to_train.values():
            targets = model.task.create_targets(self.raw_df, base_price_col='close')
            all_targets_list.append(targets)
            
        # Nối tất cả các target vào DF gốc để tạo ra một DF hoàn chỉnh
        self.df_with_targets = pd.concat([self.raw_df] + all_targets_list, axis=1)
        print(f"All targets created. New DataFrame shape: {self.df_with_targets.shape}")

    def run_feature_selection(self, weights: Dict, bonus_features: List[str], bonus_multiplier: float):
        """
        Chạy lựa chọn đặc trưng cho tất cả các cặp (Model, Task) đã đăng ký.
        """
        info("--- STEP 2: Running feature selection for all tasks ---")
        feature_cols = [c for c in self.raw_df.columns if c != 'ticker']

        for id, model in self.models_to_train.items():
            info(f"- Selecting features for task: {id}")
            task = model.task
            if task.task_id in self.feature_selected_tasks:
                info('- This task is runned feature selection')
                continue
            
            target_col = task.target_for_selection
            temp_df = self.df_with_targets.dropna(subset=[target_col])
            
            X_fs = temp_df[feature_cols]
            y_fs = temp_df[target_col]
            
            ranks_df = get_ensemble_feature_ranks(X_fs, y_fs, task_type=task.task_type)
            ranked_df = get_ranked_features(ranks_df, weights, bonus_features, bonus_multiplier)
            
            selected = select_k_plus_l_features(ranked_df, task.non_cdl_features_cnt, task.cdl_features_cnt)
            
            # Gán danh sách feature đã chọn vào Task (vì nó thuộc về định nghĩa bài toán)
            task.selected_features = selected
            self.feature_selected_tasks.add(task.task_id)

    def split_data(self, train_test_split_date: datetime, test_last_date: datetime = datetime.now()):
        """Chia dữ liệu đã có target thành tập train và test."""
        info("--- STEP 3: Splitting data into train and test sets ---")
        if self.df_with_targets is None:
            raise RuntimeError("Targets must be prepared before splitting data. Run `prepare_all_targets()` first.")
        self._train_df, self._test_df = train_test_split(self.df_with_targets, train_test_split_date, test_last_date)
        print(f"Train set shape: {self._train_df.shape}, Test set shape: {self._test_df.shape}")

    def run_walk_forward_validation(self, validation_months: int):
        """Chạy Walk-Forward Validation cho tất cả các model."""
        info("--- STEP 4: Running Walk-Forward Validation ---")
        if self._train_df is None:
            raise RuntimeError("Data must be split before running validation. Run `split_data()` first.")

        for id, model in self.models_to_train.items():
            task = model.task
            info(f"- Validating model for task: {id}")

            evaluation_results = []
            generator = get_walk_forward_splits(self._train_df, validation_months)

            for i, (train_fold_df, valid_fold_df) in enumerate(generator):
                X_train = train_fold_df[task.selected_features]
                y_train_df = train_fold_df[task.targets]
                X_valid = valid_fold_df[task.selected_features]
                y_valid_df = valid_fold_df[task.targets]

                y_train = y_train_df.values.ravel() if task.task_type == 'clf' else y_train_df
                y_valid = y_valid_df.values.ravel() if task.task_type == 'clf' else y_valid_df

                snapshot_id = f'model-fold-{i+1}'
                model.clone_kernel_model(snapshot_id)
                model.snapshot_fit(X_train, y_train, snapshot_id)
                
                preds = model.snapshot_predict(X_valid, snapshot_id)
                if task.task_type == 'clf':
                    score = f1_score(y_valid, preds, average='micro')
                    metric_name = 'f1_micro'
                else:
                    score = math.sqrt(mean_squared_error(y_valid, preds, multioutput='uniform_average'))
                    metric_name = 'avg_rmse'
                
                evaluation_results.append({'fold': i+1, metric_name: score})

            # Gán kết quả vào đối tượng model
            model.metrics = evaluation_results
            print(f"  - Finished validation. Collected {len(model.snapshot_models)} snapshots.")

    def run_final_training_and_registration(self, kaggle_username: str):
        """Huấn luyện model cuối cùng trên toàn bộ tập train và đăng ký lên Kaggle."""
        info("--- STEP 5: Final Training and Registration ---")
        if self._train_df is None:
            raise RuntimeError("Data must be split before final training. Run `split_data()` first.")

        for task_id, model in self.models_to_train.items():
            task = model.task
            info(f"- Finalizing model for task: {task_id}")
            
            X_final_train = self._train_df[task.selected_features]
            y_final_train_df = self._train_df[task.targets]
            y_final_train = y_final_train_df.values.ravel() if task.task_type == 'clf' else y_final_train_df
            
            X_final_test = self._test_df[task.selected_features]
            y_final_test_df = self._test_df[task.targets]
            y_final_test = y_final_test_df.values.ravel() if task.task_type == 'clf' else y_final_test_df
            
            model.fit(X_final_train, y_final_train)
            
            y_pred_test = model.predict(X_final_test)
            
            if task.task_type == 'clf':
                score = f1_score(y_final_test, y_pred_test, average='micro')
                metric_name = 'f1_micro'
            else:
                score = math.sqrt(mean_squared_error(y_valid, preds, multioutput='uniform_average'))
                metric_name = 'avg_rmse'
                
            model.metrics.append({'fold': 'all', metric_name: score})
            
            # Ra lệnh cho model tự đăng ký
            model.register_model_to_kaggle(kaggle_username=kaggle_username)