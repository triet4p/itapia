import math
from typing import Generator, List, Literal, Tuple
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import f1_score, mean_squared_error
from sklearn.multioutput import MultiOutputRegressor
from app.forecasting.model import ForecastingModel, ScikitLearnForecastingModel
from lightgbm import LGBMClassifier, LGBMRegressor

class OptunaObjective:
    def __init__(self, model: ForecastingModel,
                 full_df: pd.DataFrame,
                 direction: Literal['minimize', 'maximize'],
                 generator: Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None],
                 time_weighted: Literal['balance', 'new-prior'],
                 weight_bias: int = 1,
                 max_cv: int|None = 3):
        self.model = model
        if self.model.task is None:
            raise ValueError('Model must have been assigned to solve a task!')
        self.full_df = full_df
        self.direction = direction
        self.cvs = self._store_cv(generator, max_cv)
        self.time_weighted = time_weighted
        if time_weighted == 'new-prior':
            self.weight_bias = weight_bias
        else:
            self.weight_bias = 0
        
    def __call__(self, trial) -> float:
        pass
    
    def _cal_metric(self, y_true, y_pred) -> float:
        pass
    
    def _store_cv(self, generator: Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None],
                  max_cv: int|None):
        cvs: List[Tuple[pd.DataFrame, pd.DataFrame]] = []
        for train_fold_df, valid_fold_df in generator:
            cvs.append((train_fold_df, valid_fold_df))
        return cvs if max_cv is None else cvs[-max_cv:]
    
    def _run_validate_kernel_model(self, kernel_model) -> float:
        task = self.model.task
        evaluation_results = [0]
        weighted = [1]
        
        for i, (train_fold_df, valid_fold_df) in enumerate(self.cvs):
            X_train = train_fold_df[task.selected_features]
            y_train_df = train_fold_df[task.targets]
            X_valid = valid_fold_df[task.selected_features]
            y_valid_df = valid_fold_df[task.targets]

            y_train = y_train_df.values.ravel() if task.task_type == 'clf' else y_train_df.values
            y_valid = y_valid_df.values.ravel() if task.task_type == 'clf' else y_valid_df.values

            self.model.fit_kernel_model(kernel_model, X_train, y_train)
            
            preds = self.model.predict_kernel_model(kernel_model, X_valid)
            score = self._cal_metric(y_valid, preds)
            
            evaluation_results.append(score)
            weighted.append(weighted[-1] + self.weight_bias)

        # Gán kết quả vào đối tượng model
        final_obj = np.average(evaluation_results, weights=weighted)
        return final_obj
    
class LGBMClassifierObjective(OptunaObjective):
    def __init__(self, model: ScikitLearnForecastingModel,
                 full_df: pd.DataFrame, direction: Literal['minimize', 'maximize'],
                 generator: Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None],
                 time_weighted: Literal['balance', 'new-prior'],
                 weight_bias: int = 1,
                 max_cv: int|None = 3):
        super().__init__(model, full_df, direction, generator, time_weighted, weight_bias, max_cv)
    
    def _cal_metric(self, y_true, y_pred):
        return f1_score(y_true, y_pred, average='weighted')
    
    def __call__(self, trial):
        params = {
            # --- Các tham số cố định ---
            'objective': trial.suggest_categorical('objective', ['multiclass']),  # Hoặc 'binary' tùy thuộc vào bài toán
            'n_jobs': trial.suggest_categorical('n_jobs', [-1]),
            'random_state': trial.suggest_categorical('random_state', [42]),
            'verbose': trial.suggest_categorical('verbose', [-1]),
            
            # --- Các tham số được Optuna tối ưu ---
            # np.arange(32, 300, 7) -> suggest_int(low, high, step)
            'num_leaves': trial.suggest_int('num_leaves', 32, 298, step=7),
            
            # loguniform(1e-5, 4) -> suggest_float(low, high, log=True)
            'reg_lambda': trial.suggest_float('reg_lambda', 1e-5, 4.0, log=True),
            'reg_alpha': trial.suggest_float('reg_alpha', 1e-5, 4.0, log=True),
            
            # np.arange(50, 541, 40) -> suggest_int(low, high, step)
            'n_estimators': trial.suggest_int('n_estimators', 50, 530, step=40),
            
            # loguniform(0.001, 0.2) -> suggest_float(low, high, log=True)
            'learning_rate': trial.suggest_float('learning_rate', 0.002, 0.2, log=True),
            
            # np.arange(15, 55, 4) -> suggest_int(low, high, step)
            'max_depth': trial.suggest_int('max_depth', 15, 51, step=4),
            
            # loguniform(1e-8, 0.1) -> suggest_float(low, high, log=True)
            'min_split_gain': trial.suggest_float('min_split_gain', 1e-8, 0.1, log=True),
            
            # loguniform(1e-4, 0.1) -> suggest_float(low, high, log=True)
            'min_child_weight': trial.suggest_float('min_child_weight', 1e-4, 0.1, log=True),
            
            # np.arange(8, 30, 4) -> suggest_int(low, high, step)
            'min_child_samples': trial.suggest_int('min_child_samples', 8, 28, step=4),
            
            # loguniform(0.25, 1) -> suggest_float(low, high, log=True)
            'subsample': trial.suggest_float('subsample', 0.25, 1.0, log=True),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.25, 1.0, log=True),
            'max_bin': trial.suggest_categorical('max_bin', [63, 255, 511])
        }
        
        kernel_model = LGBMClassifier(**params)
        return self._run_validate_kernel_model(kernel_model)
    
class MultiOutLGBMRegressionObjective(OptunaObjective):
    def __init__(self, model: ForecastingModel,
                 full_df: pd.DataFrame,
                 direction: Literal['minimize', 'maximize'],
                 generator: Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None],
                 time_weighted: Literal['balance', 'new-prior'],
                 weight_bias: int = 1,
                 max_cv: int|None = 3):
        super().__init__(model, full_df, direction, generator, time_weighted, weight_bias, max_cv)
        
    def _cal_metric(self, y_true, y_pred):
        return math.sqrt(mean_squared_error(y_true, y_pred, multioutput='uniform_average'))
        
    def __call__(self, trial):
        params = {
            # --- Các tham số cố định ---
            'objective': trial.suggest_categorical('objective', ['regression_l1']),  # Hoặc 'binary' tùy thuộc vào bài toán
            'n_jobs': trial.suggest_categorical('n_jobs', [1]),
            'random_state': trial.suggest_categorical('random_state', [42]),
            'verbose': trial.suggest_categorical('verbose', [-1]),

            # --- Các tham số được Optuna tối ưu ---
            'num_leaves': trial.suggest_int('num_leaves', 32, 298, step=7),
            'reg_lambda': trial.suggest_float('reg_lambda', 1e-5, 5.0, log=True),
            'reg_alpha': trial.suggest_float('reg_alpha', 1e-5, 5.0, log=True),
            'n_estimators': trial.suggest_int('n_estimators', 50, 530, step=40),
            'learning_rate': trial.suggest_float('learning_rate', 0.002, 0.2, log=True),
            'max_depth': trial.suggest_int('max_depth', 15, 51, step=4),
            'min_split_gain': trial.suggest_float('min_split_gain', 1e-8, 0.1, log=True),
            'min_child_weight': trial.suggest_float('min_child_weight', 1e-4, 0.1, log=True),
            'min_child_samples': trial.suggest_int('min_child_samples', 8, 28, step=4),
            'subsample': trial.suggest_float('subsample', 0.25, 1.0, log=True),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.25, 1.0, log=True),
            'max_bin': trial.suggest_categorical('max_bin', [63, 255, 511])
        }

        # 2. Tạo đối tượng model cho trial này
        # Tạo LGBMRegressor cơ sở
        base_estimator = LGBMRegressor(**params)
        # Bọc nó trong MultiOutputRegressor
        kernel_model = MultiOutputRegressor(estimator=base_estimator, n_jobs=-1)
        return self._run_validate_kernel_model(kernel_model)
    

def get_best_params_for_kernel_model(obj: OptunaObjective,
                                     n_trials: int = 500):
    study = optuna.create_study(direction=obj.direction)
    study.optimize(obj, n_trials=n_trials)
    best_params = study.best_params
    return best_params