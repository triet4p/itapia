# forecasting/task.py

import pandas as pd
from datetime import datetime

import os
import shutil
import kagglehub
import pickle
import json

from abc import ABC, abstractmethod
from typing import Literal, Dict, List

import app.core.config as cfg

class _MLTask(ABC):
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
        
        self.model = None
        self.model_name: str = None
        self.model_params: Dict = None
        self.model_class = None
        
        self.metadata = None
        self.model_snapshots = {}
        self.extra_artifacts = {}
        
    def get_metadata(self) -> Dict:
        self.metadata = {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "targets": self.targets,
            "target_for_selection": self.target_for_selection,
            "model_name": self.model_name,
            "model_params": self.model_params,
            "features": {
                "num_selected": len(self.selected_features),
                "cdl_features_cnt": self.cdl_features_cnt,
                "non_cdl_features_cnt": self.non_cdl_features_cnt
            }
        }
        return self.metadata
    
    @abstractmethod
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        pass
    
    def set_model(self, model_class, model_params: Dict, model_name: str):
        self.model = model_class(**model_params)
        self.model_class = model_class
        self.model_name = model_name
        self.model_params = model_params
    
    def register_model_to_kaggle(
        self,
        kaggle_username: str,
        model_slug: str,
        framework: str,
        variation: str,
        version_notes: str = ""
    ):
        """
        Đóng gói và tải các artifacts lên Kaggle Models sử dụng thư viện kagglehub.

        Args:
            kaggle_username (str): Tên người dùng Kaggle của bạn.
            model_slug (str): Tên định danh cho model này (ví dụ: 'itapia-clf-tech').
            framework (str): Tên framework (ví dụ: 'scikit-learn').
            variation (str): Tên biến thể (ví dụ: 'default').
            version_notes (str): Ghi chú cho phiên bản này.
            extra_artifacts (dict): Các snapshot bổ sung để lưu.
            model_snapshots (dict): Các mô hình từ các fold để lưu.
        """
        if self.model is None:
            raise TypeError('Final model must be set before registering.')

        artifact_dir = f"./{model_slug}-artifacts-to-upload"
        if os.path.exists(artifact_dir):
            shutil.rmtree(artifact_dir)
        os.makedirs(artifact_dir)
        
        print(f"[{self.task_id}] Preparing artifacts for Kaggle Hub upload...")

        try:
            # 1. Lưu tất cả artifacts vào thư mục tạm
            # (Logic lưu file không đổi so với phiên bản trước)
            with open(os.path.join(artifact_dir, cfg.MODEL_MAIN_MODEL_FILE), "wb") as f:
                pickle.dump(self.model, f)
            with open(os.path.join(artifact_dir, cfg.MODEL_FEATURES_FILE), "w") as f:
                json.dump(self.selected_features, f, indent=4)
            with open(os.path.join(artifact_dir, cfg.MODEL_METADATA_FILE), "w") as f:
                json.dump(self.get_metadata(), f, indent=4)

            # 3. Lưu các snapshot bổ sung (nếu có)
            if self.extra_artifacts:
                print("  - Saving extra snapshot artifacts...")
                for filename, obj in self.extra_artifacts.items():
                    if isinstance(obj, pd.DataFrame):
                        obj.to_csv(os.path.join(artifact_dir, f"{filename}.csv"))
                    # Thêm logic để lưu các loại file khác (ví dụ: ảnh) ở đây nếu cần

            # 4. Lưu các mô hình snapshot từ các fold (nếu có)
            if self.model_snapshots:
                snapshot_dir = os.path.join(artifact_dir, "snapshots")
                os.makedirs(snapshot_dir, exist_ok=True)
                print("  - Saving model snapshots from folds...")
                for filename, model_obj in self.model_snapshots.items():
                    with open(os.path.join(snapshot_dir, filename), "wb") as f:
                        pickle.dump(model_obj, f)

            # 2. Xác thực và tải lên
            print(f"[{self.task_id}] Uploading to Kaggle Hub...")
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
            print(f"[{self.task_id}] Successfully uploaded a new version to handle: {handle}")

        except Exception as e:
            print(f"[{self.task_id}] An error occurred during Kaggle Hub upload: {e}")
            raise
        finally:
            print(f"[{self.task_id}] Cleaning up temporary artifact directory...")
            shutil.rmtree(artifact_dir)

    def load_model_from_kaggle(
        self,
        kaggle_username: str,
        model_slug: str,
        framework: str,
        variation: str,
        version: int = None,
        save_snapshots_locally: bool = False
    ):
        """
        Tải mô hình chính và features vào bộ nhớ. Tùy chọn tải và lưu toàn bộ
        các artifacts khác vào một thư mục local để phân tích sau.

        Args:
            ...
            save_snapshots_locally (bool): Nếu True, tất cả artifacts sẽ được sao chép
                                           đến một thư mục local cố định.
        """
        try:
            # 1. Xây dựng handle và tải về vào cache của kagglehub
            handle = cfg.MODEL_HANDLE_TEMPLATE.format(
                kaggle_username=kaggle_username, model_slug=model_slug,
                framework=framework, variation=variation
            )
            if version:
                handle = f"{handle}/{version}"

            print(f"[{self.task_id}] Downloading/Fetching model from handle: {handle}...")
            # Hàm này sẽ tải về nếu chưa có, hoặc trả về đường dẫn cache nếu đã có
            model_cache_path = kagglehub.model_download(handle)
            print(f"  - Model artifacts are available at cache path: {model_cache_path}")

            # 2. Tải các artifacts chính vào bộ nhớ
            print("  - Loading main model and features into memory...")
            with open(os.path.join(model_cache_path, cfg.MODEL_MAIN_MODEL_FILE), "rb") as f:
                self.model = pickle.load(f)
            
            with open(os.path.join(model_cache_path, cfg.MODEL_FEATURES_FILE), "r") as f:
                self.selected_features = json.load(f)

            # 3. Xử lý các artifacts còn lại (nếu có yêu cầu)
            if save_snapshots_locally:
                print("  - Saving all other artifacts to local storage...")
                
                # Tạo đường dẫn lưu trữ local duy nhất cho phiên bản model này
                version_str = f"v{version}" if version else "latest"
                local_path = os.path.join(cfg.LOCAL_ARTIFACTS_BASE_PATH, model_slug, version_str)
                
                # Dọn dẹp thư mục cũ nếu có và sao chép toàn bộ nội dung từ cache
                if os.path.exists(local_path):
                    shutil.rmtree(local_path)
                
                shutil.copytree(model_cache_path, local_path)
                
                # Lưu lại đường dẫn này để hàm get_snapshot có thể sử dụng
                self.local_artifacts_path = local_path
                print(f"  - All artifacts copied to: {self.local_artifacts_path}")

            # 4. (Tùy chọn) Tải metadata vào bộ nhớ để khôi phục trạng thái
            metadata_path = os.path.join(model_cache_path, cfg.MODEL_METADATA_FILE)
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    self.metadata = json.load(f)

            print(f"[{self.task_id}] Successfully loaded main model and features.")

        except Exception as e:
            print(f"[{self.task_id}] An error occurred while loading model from Kaggle Hub: {e}")
            raise
            
    # --- HÀM MỚI ---
    def get_snapshot_model(self, fold_id: int):
        """
        Tải một mô hình snapshot cụ thể từ thư mục đã được lưu local.

        Yêu cầu `load_model_from_kaggle` phải được chạy trước với
        `save_snapshots_locally=True`.

        Args:
            fold_id (int): Số thứ tự của fold (ví dụ: 1, 2, 3...).

        Returns:
            Một đối tượng mô hình đã được huấn luyện, hoặc None nếu không tìm thấy.
        """
        if not self.local_artifacts_path:
            raise FileNotFoundError(
                "Local artifacts not found. "
                "Please run `load_model_from_kaggle` with `save_snapshots_locally=True` first."
            )
        
        # Xây dựng đường dẫn đến file snapshot
        snapshot_filename = cfg.MODEL_SNAPSHOTS_TEMPLATE.format(fold_id=fold_id)
        snapshot_full_path = os.path.join(self.local_artifacts_path, snapshot_filename)
        
        print(f"Loading snapshot model from: {snapshot_full_path}")
        
        if not os.path.exists(snapshot_full_path):
            print(f"Warning: Snapshot file not found for fold {fold_id}.")
            return None
            
        with open(snapshot_full_path, "rb") as f:
            snapshot_model = pickle.load(f)
            
        return snapshot_model
