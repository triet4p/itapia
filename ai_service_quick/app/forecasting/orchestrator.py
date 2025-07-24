import asyncio
import time
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List

from app.forecasting.task import AvailableTaskTemplate
from app.forecasting.model import ForecastingModel, ScikitLearnForecastingModel
from app.forecasting.explainer import TreeSHAPExplainer, MultiOutputTreeSHAPExplainer, SHAPExplainer

import app.core.config as cfg

from itapia_common.dblib.services import APIMetadataService

from itapia_common.dblib.schemas.reports.forecasting import (
    ForecastingReport, SingleTaskForecastReport
)

from itapia_common.dblib.cache.memory import SimpleInMemoryCache, AsyncInMemoryCache

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Forecasting Orchestrator')

# Cache tạm thời

class ForecastingOrchestrator:
    """
    Điều phối quy trình dự báo và giải thích cho một cổ phiếu duy nhất.
    """
    def __init__(self, metadata_service: APIMetadataService):
        self.metadata_service = metadata_service
        self.model_cache = AsyncInMemoryCache()
        self.explainer_cache = AsyncInMemoryCache()

    async def _get_or_load_model(self, model_template: ForecastingModel, 
                          task_template: AvailableTaskTemplate, 
                          task_id: str) -> ForecastingModel:
        """
        Lấy model từ cache. Nếu không có, tải về từ Kaggle và cache lại.
        Hàm này sẽ tự động "hồi sinh" Task từ metadata đã lưu.
        """
        model_slug = model_template.get_model_slug(task_id=task_id)

        async def model_factory():
            logger.info(f"CACHE MISS: Loading model for task '{task_id}'...")
            
            # Chạy hàm blocking trong executor
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, 
                model_template.load_model_from_kaggle, # Hàm blocking
                cfg.KAGGLE_USERNAME, task_template, task_id # Các tham số
            )
            return model_template

        return await self.model_cache.get_or_set_with_lock(model_slug, model_factory)
    
    async def _get_or_create_explainer(self, model_wrapper: ForecastingModel) -> SHAPExplainer:
        """
        Lấy explainer từ cache. Nếu không có, tạo mới và cache lại.
        """
        task = model_wrapper.task
        # Sử dụng task_id làm key vì explainer phụ thuộc vào loại task
        explainer_key = task.task_id

        async def explainer_factory():
            # Tạo explainer là CPU-bound, có thể chạy trong executor
            logger.info('CACHE MISS for Explainer')
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._create_explainer_sync, model_wrapper)
        
        return await self.explainer_cache.get_or_set_with_lock(explainer_key, explainer_factory)
    
    def _create_explainer_sync(self, model_wrapper: ForecastingModel):
        if model_wrapper.task.task_type == 'clf':
            explainer = TreeSHAPExplainer(model_wrapper)
        else: # reg
            explainer = MultiOutputTreeSHAPExplainer(model_wrapper)
        return explainer    
    
    # --- PHIÊN BẢN SYNC (WRAPPER) ---
    # --- PHIÊN BẢN SYNC (WRAPPER) - ĐÃ CẬP NHẬT ---
    def _get_or_load_model_sync(self, model_template: ForecastingModel, 
                               task_template: AvailableTaskTemplate, 
                               task_id: str) -> ForecastingModel:
        """
        Wrapper đồng bộ cho hàm async. Sử dụng event loop đang chạy.
        """
        try:
            # Lấy event loop đang hoạt động
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            # Nếu không có loop nào (ví dụ: chạy trong một script sync thuần túy)
            # thì tạo một loop mới
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Chạy coroutine trên loop đã có và chờ kết quả
        return loop.run_until_complete(
            self._get_or_load_model(model_template, task_template, task_id)
        )

    def _get_or_create_explainer_sync(self, model_wrapper: ForecastingModel) -> SHAPExplainer:
        """
        Wrapper đồng bộ cho hàm async. Sử dụng event loop đang chạy.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(
            self._get_or_create_explainer(model_wrapper)
        )
        
    def generate_report(self, latest_enriched_data: pd.DataFrame, ticker: str) -> ForecastingReport:
        """
        Hàm chính: Nhận vào 1 dòng dữ liệu và ticker, trả về một báo cáo Pydantic.
        """
        if not isinstance(latest_enriched_data, pd.DataFrame) or len(latest_enriched_data) != 1:
            raise ValueError("Input must be a DataFrame with a single row.")

        # --- BƯỚC 1: Thu thập thông tin bối cảnh ---
        sector_code = self.metadata_service.get_sector_code_of(ticker)
        logger.info(f"--- Generating Forecast Report for Ticker: {ticker} (Sector: {sector_code}) ---")

        # --- BƯỚC 2: Định nghĩa các "Công thức" Model và Task ---

        # 2c. Định nghĩa các Task Template
        tasks_to_run_config = self._get_tasks_config_for_sector(sector_code)
        
        task_reports_list: List[SingleTaskForecastReport] = []

        # --- BƯỚC 3: Lặp qua từng task ---
        for model_template, task_template, problem_id in tasks_to_run_config:
            task_id = cfg.TASK_ID_SECTOR_TEMPLATE.format(problem=problem_id, sector=sector_code)
            logger.info(f"- Processing task: {task_id}")
            
            # 3a. Lấy/Tải model. Model trả về sẽ chứa task đã được "hồi sinh"
            model_wrapper = self._get_or_load_model_sync(model_template, task_template, task_id)
            task = model_wrapper.task # Lấy ra task đã được khôi phục
            
            # 3b. Chuẩn bị dữ liệu đầu vào với các features đã được load
            X_instance = latest_enriched_data[task.selected_features]
            
            # 3c. Chạy Dự báo (đã bao gồm post-processing nếu có)
            prediction_array = model_wrapper.predict(X_instance)
            
            # 3d. Chạy Giải thích
            explainer = self._get_or_create_explainer_sync(model_wrapper)
            
            explanations = explainer.explain_prediction(X_instance)
            
            # 3e. Đóng gói kết quả vào đối tượng Pydantic
            task_report = SingleTaskForecastReport(
                task_name=task.task_id,
                task_metadata=task.get_metadata(),
                prediction=prediction_array.flatten().tolist(),
                units=task.target_units,
                evidence=explanations # Pydantic sẽ tự validate
            )
            task_reports_list.append(task_report)
            logger.info(f'- Processed task: {task_id}')
            
        # --- BƯỚC 4: Tạo báo cáo cuối cùng ---
        generated_time = datetime.now(timezone.utc)
        final_report = ForecastingReport(
            ticker=ticker.upper(),
            sector=sector_code,
            generated_at=generated_time.isoformat(),
            generated_timestamp=int(generated_time.timestamp()),
            forecasts=task_reports_list
        )
        
        logger.info('Generated report')
        
        return final_report
    
    async def preload_caches_for_all_sectors(self):
        """
        Tải trước tất cả các model và tạo các explainer cho TẤT CẢ các sector
        để làm nóng cache in-memory.
        Hàm này được thiết kế để chạy ở chế độ nền khi ứng dụng khởi động.
        """
        logger.info("--- FORECASTING: Starting pre-warming process for all models & explainers ---")
        try:
            # 1. Lấy danh sách tất cả các sector từ DB
            all_sectors = [x.sector_code for x in self.metadata_service.get_all_sectors()]
            #all_sectors = ['TECH']
            logger.info(f"Found {len(all_sectors)} sectors to pre-warm: {all_sectors}")

            # 2. Lặp qua từng sector để tải model và tạo explainer
            for sector_code in all_sectors:
                logger.info(f"  - Pre-warming for sector: {sector_code}")
                try:
                    # Lấy lại "công thức" model/task từ hàm generate_report để đảm bảo nhất quán
                    tasks_to_run_config = self._get_tasks_config_for_sector(sector_code)
                    
                    for model_template, task_template, problem_id in tasks_to_run_config:
                        task_id = cfg.TASK_ID_SECTOR_TEMPLATE.format(problem=problem_id, sector=sector_code)
                        
                        # Tải model (sẽ được cache nếu chưa có)
                        model_wrapper = await self._get_or_load_model(model_template, task_template, task_id)
                        
                        # Tạo explainer (sẽ được cache nếu chưa có)
                        await self._get_or_create_explainer(model_wrapper)
                        
                        # Thêm một chút delay để không quá tải và nhường CPU
                        time.sleep(1)
                except Exception as e:
                    logger.err(f"  - ERROR pre-warming for sector {sector_code}: {e}")
                    
        except Exception as e:
            logger.err(f"A critical error occurred during the pre-warming process: {e}")
        
        logger.info("--- FORECASTING: Pre-warming process complete ---")
    
    def _get_tasks_config_for_sector(self, sector_code: str):
        """
        Hàm private để tập trung hóa việc định nghĩa các task.
        Tránh lặp lại code giữa generate_report và preload_caches.
        """

        # Trả về cấu hình các cặp (Model Template, Task Template, Problem ID)
        return [
            (
                ScikitLearnForecastingModel(name=cfg.LGBM_MODEL_BASE_NAME, variation=cfg.MODEL_VARIATION),
                AvailableTaskTemplate.TRIPLE_BARRIER_TASK,
                cfg.TRIPLE_BARRIER_PROBLEM_ID
            ),
            (
                ScikitLearnForecastingModel(name=cfg.MULTIOUTPUT_LGBM_MODEL_BASE_NAME, variation=cfg.MODEL_VARIATION),
                AvailableTaskTemplate.NDAYS_DISTRIBUTION_TASK,
                cfg.REG_5D_DIS_PROBLEM_ID
            ),
            (
                ScikitLearnForecastingModel(name=cfg.MULTIOUTPUT_LGBM_MODEL_BASE_NAME, variation=cfg.MODEL_VARIATION),
                AvailableTaskTemplate.NDAYS_DISTRIBUTION_TASK,
                cfg.REG_20D_DIS_PROBLEM_ID
            ),
        ]