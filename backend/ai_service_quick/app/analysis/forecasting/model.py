from typing import List, Literal
import kagglehub
from datetime import datetime
import shutil
import os
import pickle
import json
import numpy as np
from sklearn.base import clone
from abc import ABC, abstractmethod

import pandas as pd

from .task import ForecastingTask, ForecastingTaskFactory, AvailableTaskTemplate
from .post_processing import PostProcessor
import app.core.config as cfg

class ForecastingModel(ABC):
    """
    A Wrapper class, which wraps around any core models to ensure extensibility and maintainability
    """
    def __init__(self, name: str,
                 framework: str,
                 kernel_model_template = None,
                 variation: str = 'original',
                 post_processors: List[PostProcessor]|None = None):
        """
        Init a forecasting model wrapper.

        Args:
            name (str): Name of model, this is an unique name to distinguind models in the same framework.
            framework (str): Framework, library that model use, like `sklearn`, `pytorch`,...
            kernel_model_template (_type_, optional): A template (class type) use to init core model. Defaults to None.
            variation (str, optional): Variation of models. Defaults to 'original'.
            post_processors (List[PostProcessor] | None, optional): Some of Post processors to transform
                output of core models, like rounding, etc. Defaults to None.
        """
        self.name = name
        self.kernel_model_template = kernel_model_template
        
        self.kernel_model = None
        
        self.framework = framework
        self.variation = variation
        
        self.task: ForecastingTask = None
        
        self.snapshot_models = {}
        self.snapshot_registry = {}
        self.metrics = []
        
        self.post_processors = post_processors
        
        self.model_cache_path: str = ""
        
    def assign_task(self, task: ForecastingTask):
        self.task = task
    
    def set_trained_kernel_model(self, trained_kernel_model):
        self.kernel_model_template = trained_kernel_model
        
    def get_model_slug(self, task_id: str = None) -> str:
        """
        Get model slug to identify model in Kaggle. A Slug template is in format in `app.core.config.MODEL_SLUG_TEMPLATE`

        Normally, a model slug look like `{model_name}-{task_id}
        
        Args:
            task_id (str, optional): Id of task which model solve. Defaults to None.

        Returns:
            str: Model slug
        """
        if task_id is not None:
            return cfg.MODEL_SLUG_TEMPLATE.format(id=f"{self.name}-{task_id.lower().replace('_','-')}")
        return cfg.MODEL_SLUG_TEMPLATE.format(id=f"{self.name}-{self.task.task_id.lower().replace('_','-')}")
    
    def get_metadata(self):
        return {
            'kernel_model': {
                'name': self.name,
                'class': type(self.kernel_model_template).__name__
            },
            'task': self.task.get_metadata(),
            'snapshots': {
                'cnt': len(self.snapshot_models.keys()),
                'details': self.snapshot_registry
            },
            'metrics': self.metrics
        }
        
    def register_model_to_kaggle(
        self,
        kaggle_username: str,
        version_notes: str = "",
        include_snapshots: bool = False
    ):
        """
        Package and upload all artifacts of Forecasting Model to Kaggle Models.

        Args:
            kaggle_username (str): Your kaggle username.
            version_notes (str): Notes for this upload.
            include_snapshots (bool): Determine whether snapshots will be included in artifacts to upload. 
                This is an arg that is usually decided based on model variation.
        """
        if self.kernel_model is None:
            raise TypeError('Final model must be set before registering.')
        
        model_slug = self.get_model_slug()
        framework = self.framework
        variation = self.variation
        
        artifact_dir = cfg.LOCAL_ARTIFACTS_BASE_PATH
        if os.path.exists(artifact_dir):
            shutil.rmtree(artifact_dir)
        os.makedirs(artifact_dir)
        
        print(f"[{self.name}] Preparing artifacts for Kaggle Hub upload...")

        try:
            # 1. Save all artifacts in temp dir.
            with open(os.path.join(artifact_dir, cfg.MODEL_MAIN_MODEL_FILE), "wb") as f:
                pickle.dump(self.kernel_model, f)
            with open(os.path.join(artifact_dir, cfg.MODEL_METADATA_FILE), "w") as f:
                json.dump(self.get_metadata(), f, indent=4)
                
            if self.snapshot_models and include_snapshots:
                snapshot_dir = os.path.join(artifact_dir, "snapshots")
                os.makedirs(snapshot_dir, exist_ok=True)
                print("  - Saving model snapshots from folds...")
                for snapshot_id, model_obj in self.snapshot_models.items():
                    filename = f'{snapshot_id}.pkl'
                    with open(os.path.join(snapshot_dir, filename), "wb") as f:
                        pickle.dump(model_obj, f)

            # 2. Authentication and upload
            print(f"[{self.name}] Uploading to Kaggle Hub...")
            kagglehub.login()

            # Xây dựng handle theo đúng cấu trúc mới
            handle = cfg.MODEL_HANDLE_TEMPLATE.format(
                kaggle_username=kaggle_username,
                model_slug=model_slug,
                framework=framework,
                variation=variation
            )
            
            if not version_notes:
                version_notes = f"Training run on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            kagglehub.model_upload(
                handle=handle,
                local_model_dir=artifact_dir,
                version_notes=version_notes
            )
            print(f"[{self.name}] Successfully uploaded a new version to handle: {handle}")

        except Exception as e:
            print(f"[{self.name}] An error occurred during Kaggle Hub upload: {e}")
            raise
        finally:
            print(f"[{self.name}] Cleaning up temporary artifact directory...")
            shutil.rmtree(artifact_dir)
            
    def load_model_from_kaggle(
        self,
        kaggle_username: str,
        task_template: AvailableTaskTemplate,
        task_id: str,
        version: int = None,
        load_snapshot_on_mem: bool = False
    ):
        """
        Download and restore history state of a Forecasting Model from Kaggle.

        Args:
            kaggle_username (str): Your kaggle username.
            task_template (AvailableTaskTemplate): Template of task that model solve. Use to restore task state of model.
            task_id (str): ID of task that model solve. Use to recreate task of model.
            version (int, optional): Version number to download, if None, latest version will be downloaded. Defaults to None.
            load_snapshot_on_mem (bool, optional): Load snapshots of model into memory after download. Defaults to False. 
        """
        # Get important infomation
        model_slug = self.get_model_slug(task_id)
        framework = self.framework
        variation = self.variation

        try:
            # 2. Create handle and download
            handle = cfg.MODEL_HANDLE_TEMPLATE.format(
                kaggle_username=kaggle_username, model_slug=model_slug,
                framework=framework, variation=variation
            )
            if version:
                handle = f"{handle}/{version}"

            print(f"[{self.name}] Downloading model from handle: {handle}...")
            model_cache_path = kagglehub.model_download(handle)
            print(f"  - Model downloaded to cache path: {model_cache_path}")
            self.model_cache_path = model_cache_path
            
            # 3. Load artifacts into property of this instance
            print("  - Loading artifacts into model object...")

            # Load kernel model
            main_model_path = os.path.join(model_cache_path, cfg.MODEL_MAIN_MODEL_FILE)
            if os.path.exists(main_model_path):
                with open(main_model_path, "rb") as f:
                    self.kernel_model = pickle.load(f)
                    self.kernel_model_template = self.clone_unfitted_kernel_model()
                print(f"  - Successfully loaded main kernel model: {type(self.kernel_model)}")
            else:
                raise FileNotFoundError(f"Main model file '{cfg.MODEL_MAIN_MODEL_FILE}' not found in downloaded artifacts.")
            
            # Load metadata
            metadata_path = os.path.join(model_cache_path, cfg.MODEL_METADATA_FILE)
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    full_metadata: dict = json.load(f)
                
                # Load metrics
                self.metrics = full_metadata.get("metrics", [])
                
                # Extract metadata of task
                task_metadata = full_metadata.get('task')
                
                if task_metadata:
                    self.task = ForecastingTaskFactory.create_task(task_template, task_id, task_metadata)
                else:
                    print("Warning: 'task' key not found in metadata.json. Task state not restored.")
                    
                self.snapshot_registry = full_metadata.get('snapshots', {}).get('details', {})
            else:
                print("Warning: metadata.json not found. Task state not restored.")
                
            # Load snapshots if needed
            if load_snapshot_on_mem:
                self.load_all_snapshot_from_disk()

            print(f"[{self.name}] Model loading complete with task {self.task.task_id}.")

        except Exception as e:
            print(f"[{self.name}] An error occurred while loading model from Kaggle Hub: {e}")
            raise
        finally:
            print(f"[{self.name}] Cleaning up temporary artifact directory...")
            #shutil.rmtree(model_cache_path)
        
    @abstractmethod
    def clone_unfitted_kernel_model(self):
        """
        Clone an unfitted model from kernel model. That method will be return a core models with same type, parameters,
        hyperparameters with kernel model, but unfitted.
        """
        pass
    
    @abstractmethod
    def fit_kernel_model(self, kernel_model, X: pd.DataFrame, y: pd.Series|pd.DataFrame) -> None:
        """
        Fit a kernel model.
        """
        pass
    
    @abstractmethod
    def predict_kernel_model(self, kernel_model, X: pd.DataFrame) -> np.ndarray:
        """
        Predict using a kernel model.
        """
        pass
        
    def fit(self, X: pd.DataFrame, y: pd.Series|pd.DataFrame, snapshot_id: str|None = None):
        """
        Fit a specific core model (kernel model or snapshot).

        Args:
            X (pd.DataFrame): Training data
            y (pd.Series | pd.DataFrame): Training labels
            snapshot_id (str | None, optional): ID of Core model to use. If None, use main kernel model.
                Defaults to None.
        """
        kernel_model = self.clone_unfitted_kernel_model()
        self.fit_kernel_model(kernel_model, X, y)
        if snapshot_id is not None:
            self.snapshot_models[snapshot_id] = kernel_model
        else:
            self.kernel_model = kernel_model

    def predict(self, X: pd.DataFrame, snapshot_id: str|None = None) -> np.ndarray:
        """
        Predict using a specific core model (kernel model or snapshot).

        Args:
            X (pd.DataFrame): Test data
            snapshot_id (str | None, optional): ID of Core model to use. If None, use main kernel model.
                Defaults to None.
        """
        if snapshot_id is not None:
            if snapshot_id not in self.snapshot_models:
                raise KeyError(f"Snapshot ID '{snapshot_id}' not found.")
            model_to_use = self.snapshot_models[snapshot_id]
        else:
            if self.kernel_model is None:
                raise TypeError("Main kernel model has not been trained yet. Call fit() without a snapshot_id.")
            model_to_use = self.kernel_model
        
        prediction = self.predict_kernel_model(model_to_use, X)
        if self.post_processors is not None:
            for processor in self.post_processors:
                prediction = processor.apply(prediction)
                
        return prediction
    
    def register_snapshot(self, snapshot_id: str, available_test_time: datetime):
        """
        Register a snapshot with this available test time. To avoid future bias, 
        this snapshot model should only be used to predict data that is earlier than `available_test_time`
        """
        available_test_ts = int(available_test_time.timestamp())
        self.snapshot_registry[snapshot_id] = available_test_ts
        
    def get_snapshot_by_test_time(self, test_time: datetime,
                                  match_type: Literal['first', 'last'] = 'last') -> str:
        """
        Select a snapshot which is best match with test time. 
        A model is best-fit if its `available_test_time` is 
        later than `test_time` and its `available_test_time` is earliest or lastest,
        based on `match_type` arg.
        
        Raises:
            KeyError: If no model is found.
        """
        test_ts = int(test_time.timestamp())
        found_ids = []
        
        for snapshot_id, av_test_ts in self.snapshot_registry.items():
            if test_ts >= av_test_ts:
                found_ids.append(snapshot_id)
            
        if len(found_ids) == 0:
            raise KeyError('Not found any snapshot model.')
        
        return found_ids[0] if match_type == 'first' else found_ids[-1]
        
    def load_all_snapshot_from_disk(self):
        if self.model_cache_path is None:
            raise FileNotFoundError("  - No snapshots directory found, skipping snapshot loading.")
        self.snapshot_models = {}  
        snapshot_keys = list(self.snapshot_registry.keys())
        snapshot_dir = os.path.join(self.model_cache_path, "snapshots")
        if os.path.exists(snapshot_dir):
            print("  - Loading snapshot models from folds...")
            for snapshot_key in snapshot_keys:
                with open(os.path.join(snapshot_dir, f'{snapshot_key}.pkl'), "rb") as f:
                    self.snapshot_models[snapshot_key] = pickle.load(f)
            print(f"  - Successfully loaded {len(self.snapshot_models)} snapshot models.")
        else:
            raise FileNotFoundError("  - No snapshots directory found, skipping snapshot loading.")
        
    def is_loaded_snapshots(self):
        if not self.snapshot_models:
            return False
        if set(self.snapshot_models.keys()) != set(self.snapshot_registry.keys()):
            return False
        
        return True
        
    def clear_all_snapshot(self):
        self.snapshot_models.clear()
    
class ScikitLearnForecastingModel(ForecastingModel):
    def __init__(self, name, kernel_model_template = None, variation = 'original',
                 post_processors: list[PostProcessor]|None = None):
        super().__init__(name, kernel_model_template=kernel_model_template, 
                         framework='scikitLearn', variation=variation,
                         post_processors=post_processors)
        
    def clone_unfitted_kernel_model(self):
        if self.kernel_model_template is not None:
            return clone(self.kernel_model_template)
        if self.kernel_model is not None:
            return clone(self.kernel_model)
        raise ValueError("Not found any template!")
    
    def fit_kernel_model(self, kernel_model, X, y):
        kernel_model.fit(X, y)
    
        
    def predict_kernel_model(self, kernel_model, X):
        return kernel_model.predict(X)