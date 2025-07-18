import kagglehub
from datetime import datetime
import shutil
import os
import pickle
import json

from abc import ABC, abstractmethod

import pandas as pd

from app.forecasting.task import ForecastingTask
import app.core.config as cfg

class ForecastingModel(ABC):
    def __init__(self, name: str,
                 kernel_model_class, kernel_model_params: dict,
                 framework: str,
                 variation: str = 'original'):
        self.name = name
        self.kernel_model_class = kernel_model_class
        self.kernel_model_params = kernel_model_params
        
        self.kernel_model = None
        
        self.framework = framework
        self.variation = variation
        
        self.task: ForecastingTask = None
        
        self.snapshot_models = {}
        self.metrics = []
        
    def assign_task(self, task: ForecastingTask):
        self.task = task
        
    def clone_kernel_model(self, snapshot_id: str|None):
        if snapshot_id is None:
            self.kernel_model = self.kernel_model_class(self.kernel_model_params)
        else:
            self.snapshot_models[snapshot_id] = self.kernel_model_class(self.kernel_model_params)
    
    def set_trained_kernel_model(self, trained_kernel_model):
        self.kernel_model = trained_kernel_model
        
    def get_model_slug(self):
        return cfg.MODEL_SLUG_TEMPLATE.format(id=f'{self.name}-{self.task.task_id.lower().replace('_','-')}')
    
    def get_metadata(self):
        return {
            'kernel_model': {
                'name': self.name,
                'params': self.kernel_model_params
            },
            'task': self.task.get_metadata(),
            'snapshots': {
                'cnt': len(self.snapshot_models.keys()),
                'details': list(self.snapshot_models.keys())
            },
            'metrics': self.metrics
        }
        
    def register_model_to_kaggle(
        self,
        kaggle_username: str,
        version_notes: str = ""
    ):
        """
        Đóng gói và tải các artifacts lên Kaggle Models sử dụng thư viện kagglehub.

        Args:
            kaggle_username (str): Tên người dùng Kaggle của bạn.
            version_notes (str): Ghi chú cho phiên bản này.
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
            # 1. Lưu tất cả artifacts vào thư mục tạm
            # (Logic lưu file không đổi so với phiên bản trước)
            with open(os.path.join(artifact_dir, cfg.MODEL_MAIN_MODEL_FILE), "wb") as f:
                pickle.dump(self.kernel_model, f)
            with open(os.path.join(artifact_dir, cfg.MODEL_METADATA_FILE), "w") as f:
                json.dump(self.get_metadata(), f, indent=4)
                
            if self.snapshot_models:
                snapshot_dir = os.path.join(artifact_dir, "snapshots")
                os.makedirs(snapshot_dir, exist_ok=True)
                print("  - Saving model snapshots from folds...")
                for snapshot_id, model_obj in self.snapshot_models.items():
                    filename = f'{snapshot_id}.pkl'
                    with open(os.path.join(snapshot_dir, filename), "wb") as f:
                        pickle.dump(model_obj, f)

            # 2. Xác thực và tải lên
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
        version: int = None
    ):
        """
        Tải về các artifacts từ Kaggle Hub và khôi phục trạng thái của ForecastingModel.
        Hàm này tải mô hình chính (kernel_model) và tất cả các mô hình snapshot.

        Args:
            kaggle_username (str): Tên người dùng Kaggle của bạn.
            version (int, optional): Số phiên bản cụ thể cần tải. Nếu None, tải phiên bản mới nhất.
        """
        # Xây dựng các thông tin cần thiết từ chính object
        model_slug = self.get_model_slug()
        framework = self.framework
        variation = self.variation
        
        # 1. Tạo thư mục tạm để tải về
        download_dir = f"./{model_slug}_download"
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
        os.makedirs(download_dir)
        
        unzip_path = os.path.join(download_dir, "unzipped")

        try:
            # 2. Xây dựng handle và tải về file ZIP
            handle = cfg.MODEL_HANDLE_TEMPLATE.format(
                kaggle_username=kaggle_username, model_slug=model_slug,
                framework=framework, variation=variation
            )
            if version:
                handle = f"{handle}/{version}"

            print(f"[{self.name}] Downloading model from handle: {handle}...")
            model_cache_path = kagglehub.model_download(handle)
            print(f"  - Model downloaded to cache path: {model_cache_path}")

            # 3. Tải các artifacts vào các thuộc tính của instance
            print("  - Loading artifacts into model object...")

            # Tải mô hình chính (kernel_model)
            main_model_path = os.path.join(model_cache_path, cfg.MODEL_MAIN_MODEL_FILE)
            if os.path.exists(main_model_path):
                with open(main_model_path, "rb") as f:
                    self.kernel_model = pickle.load(f)
                print(f"  - Successfully loaded main kernel model: {type(self.kernel_model)}")
            else:
                raise FileNotFoundError(f"Main model file '{cfg.MODEL_MAIN_MODEL_FILE}' not found in downloaded artifacts.")

            # Tải các mô hình snapshot
            self.snapshot_models = {}  # Xóa các snapshot cũ nếu có
            snapshot_dir = os.path.join(model_cache_path, "snapshots")
            if os.path.exists(snapshot_dir):
                print("  - Loading snapshot models from folds...")
                snapshot_files = [f for f in os.listdir(snapshot_dir) if f.endswith(".pkl")]
                for filename in snapshot_files:
                    snapshot_key = os.path.splitext(filename)[0]  # Lấy tên file không có .pkl
                    with open(os.path.join(snapshot_dir, filename), "rb") as f:
                        self.snapshot_models[snapshot_key] = pickle.load(f)
                print(f"  - Successfully loaded {len(self.snapshot_models)} snapshot models.")
            else:
                print("  - No snapshots directory found, skipping snapshot loading.")

            print(f"[{self.name}] Model loading complete.")

        except Exception as e:
            print(f"[{self.name}] An error occurred while loading model from Kaggle Hub: {e}")
            raise
        
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series|pd.DataFrame):
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> (pd.DataFrame|pd.Series):
        pass
    
    @abstractmethod
    def snapshot_fit(self, X: pd.DataFrame, y: pd.Series|pd.DataFrame, snapshot_id: str):
        pass
    
    @abstractmethod
    def snapshot_predict(self, X: pd.DataFrame, snapshot_id: str) -> (pd.DataFrame|pd.Series):
        pass
    
class ScikitLearnForecastingModel(ForecastingModel):
    def __init__(self, name, kernel_model_class, kernel_model_params, variation = 'original'):
        super().__init__(name, kernel_model_class, kernel_model_params, 
                         framework='scikitLearn', variation=variation)
        
    def fit(self, X, y):
        self.kernel_model = self.clone_kernel_model()
        self.kernel_model.fit(X, y)
    
    def predict(self, X):
        return self.kernel_model.predict(X)
    
    def snapshot_fit(self, X, y, snapshot_id):
        if snapshot_id not in self.snapshot_models.keys():
            self.clone_kernel_model(snapshot_id)
        self.snapshot_models[snapshot_id].fit(X, y)
    
    def snapshot_predict(self, X, snapshot_id):
        return self.snapshot_models[snapshot_id].predict(X)