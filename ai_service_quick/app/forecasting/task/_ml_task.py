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
        
    def get_metadata(self) -> Dict:
        return {
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
    
    @abstractmethod
    def create_targets(self, df: pd.DataFrame, base_price_col: str) -> pd.DataFrame:
        pass
    
    def set_model(self, model_class, model_params: Dict, model_name: str):
        self.model = model_class(**model_params)
        self.model_name = model_name
        self.model_params = model_params
    
    def register_model_to_kaggle(
        self,
        kaggle_username: str,
        model_slug: str,
        framework: str = "scikit-learn",
        variation: str = "default",
        version_notes: str = "",
        extra_artifacts: dict = None,
        model_snapshots: dict = None
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
            with open(os.path.join(artifact_dir, "final-model.pkl"), "wb") as f:
                pickle.dump(self.model, f)
            with open(os.path.join(artifact_dir, "features.json"), "w") as f:
                json.dump(self.selected_features, f, indent=4)
            with open(os.path.join(artifact_dir, "metadata.json"), "w") as f:
                json.dump(self.get_metadata(), f, indent=4)

            # 3. Lưu các snapshot bổ sung (nếu có)
            if extra_artifacts:
                print("  - Saving extra snapshot artifacts...")
                for filename, obj in extra_artifacts.items():
                    if isinstance(obj, pd.DataFrame):
                        obj.to_csv(os.path.join(artifact_dir, f"{filename}.csv"))
                    # Thêm logic để lưu các loại file khác (ví dụ: ảnh) ở đây nếu cần

            # 4. Lưu các mô hình snapshot từ các fold (nếu có)
            if model_snapshots:
                snapshot_dir = os.path.join(artifact_dir, "snapshots")
                os.makedirs(snapshot_dir, exist_ok=True)
                print("  - Saving model snapshots from folds...")
                for filename, model_obj in model_snapshots.items():
                    with open(os.path.join(snapshot_dir, filename), "wb") as f:
                        pickle.dump(model_obj, f)

            # 2. Xác thực và tải lên
            print(f"[{self.task_id}] Uploading to Kaggle Hub...")
            kagglehub.login()

            # Xây dựng handle theo đúng cấu trúc mới
            handle = f"{kaggle_username}/{model_slug}/{framework}/{variation}"
            
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
            #shutil.rmtree(artifact_dir)

    # --- HÀM LOAD ĐÃ VIẾT LẠI HOÀN TOÀN ---
    def load_model_from_kaggle(
        self,
        kaggle_username: str,
        model_slug: str,
        framework: str = "scikit-learn",
        variation: str = "default",
        version: int = None # Giữ lại để tương thích, nhưng kagglehub.model_download ko dùng
    ):
        """
        Tải về và khôi phục trạng thái task từ Kaggle Models sử dụng kagglehub.

        Args:
            kaggle_username (str): Tên người dùng Kaggle của bạn.
            model_slug (str): Tên định danh cho model này (ví dụ: 'itapia-clf-tech').
            framework (str): Tên framework (ví dụ: 'scikit-learn').
            variation (str): Tên biến thể (ví dụ: 'default').
            version (int): Số phiên bản cụ thể (hiện không được hỗ trợ bởi hàm download).
        """
        try:
            # 1. Xây dựng handle và tải về
            handle = f"{kaggle_username}/{model_slug}/{framework}/{variation}"
            if version:
                 handle = f"{handle}/{version}"

            print(f"[{self.task_id}] Downloading model from handle: {handle}...")
            # kagglehub.model_download sẽ tải về cache và trả về đường dẫn
            model_path = kagglehub.model_download(handle)
            print(f"  - Model downloaded to cache path: {model_path}")

            # 2. Tải các artifacts từ đường dẫn đã cache
            print("  - Loading artifacts into task object...")
            with open(os.path.join(model_path, "final_model.pkl"), "rb") as f:
                self.model = pickle.load(f)
            
            with open(os.path.join(model_path, "features.json"), "r") as f:
                self.selected_features = json.load(f)
            
            # (Tùy chọn) Tải metadata để khôi phục trạng thái
            if os.path.exists(os.path.join(model_path, "metadata.json")):
                 with open(os.path.join(model_path, "metadata.json"), "r") as f:
                    metadata = json.load(f)
                    self.model_name = metadata.get("model_name", self.model_name)
                    self.model_params = metadata.get("model_params", self.model_params)

            print(f"[{self.task_id}] Successfully loaded model and {len(self.selected_features)} features.")

        except Exception as e:
            print(f"[{self.task_id}] An error occurred while loading model from Kaggle Hub: {e}")
            raise