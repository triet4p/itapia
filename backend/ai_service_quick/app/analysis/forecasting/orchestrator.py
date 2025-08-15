import asyncio
from functools import partial
import time
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List

from app.core.exceptions import PreloadCacheError

from .task import AvailableTaskTemplate
from .model import ForecastingModel, ScikitLearnForecastingModel
from .explainer import TreeSHAPExplainer, MultiOutputTreeSHAPExplainer, SHAPExplainer

import app.core.config as cfg

from itapia_common.schemas.entities.analysis.forecasting import (
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
    def __init__(self):
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
    
    async def _get_or_create_explainer(self, model_wrapper: ForecastingModel, snapshot_id: str|None=None) -> SHAPExplainer:
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
            return await loop.run_in_executor(None, self._create_explainer_sync, model_wrapper, snapshot_id)
        
        return await self.explainer_cache.get_or_set_with_lock(explainer_key, explainer_factory)
    
    def _create_explainer_sync(self, model_wrapper: ForecastingModel, snapshot_id: str|None = None):
        if model_wrapper.task.task_type == 'clf':
            explainer = TreeSHAPExplainer(model_wrapper, snapshot_id)
        else: # reg
            explainer = MultiOutputTreeSHAPExplainer(model_wrapper, snapshot_id)
        return explainer    
        
    async def _process_single_task(self, model_template: ForecastingModel, 
                                   task_template: AvailableTaskTemplate, 
                                   problem_id: str,
                                   sector_code: str,
                                   latest_enriched_data: pd.DataFrame) -> SingleTaskForecastReport:
        """
        Worker coroutine: Xử lý một task dự báo duy nhất một cách hoàn toàn bất đồng bộ.
        """
        task_id = cfg.TASK_ID_SECTOR_TEMPLATE.format(problem=problem_id, sector=sector_code)
        
        # 1. Lấy model và explainer (đã là async, rất tốt)
        model_wrapper = await self._get_or_load_model(model_template, task_template, task_id)
        explainer = await self._get_or_create_explainer(model_wrapper)
        
        task = model_wrapper.task
        X_instance = latest_enriched_data[task.selected_features]
        
        loop = asyncio.get_running_loop()

        # 2. Chạy các tác vụ CPU-bound song song trong executor
        #    (Vì predict và explain thường độc lập, chúng có thể chạy cùng lúc)
        logger.info(f"  - Running predict & explain for task: {task_id}")
        
        # Sử dụng functools.partial để gói các hàm có tham số
        predict_func = partial(model_wrapper.predict, X_instance)
        explain_func = partial(explainer.explain_prediction, X_instance)

        prediction_array, explanations = await asyncio.gather(
            loop.run_in_executor(None, predict_func),
            loop.run_in_executor(None, explain_func)
        )
        
        # 3. Đóng gói kết quả (chạy rất nhanh)
        task_report = SingleTaskForecastReport(
            task_name=task.task_id,
            task_metadata=task.get_metadata_for_plain(),
            prediction=prediction_array.flatten().tolist(),
            units=task.target_units,
            evidence=explanations
        )
        logger.info(f"  - Completed task: {task_id}")
        return task_report
        
    async def generate_report(self, latest_enriched_data: pd.DataFrame, ticker: str, sector: str):
        """
        Hàm chính (phiên bản async): Tạo báo cáo dự báo đầy đủ bằng cách
        chạy song song các task phân tích khác nhau.
        """
        if not isinstance(latest_enriched_data, pd.DataFrame) or len(latest_enriched_data) != 1:
            raise ValueError("Input must be a DataFrame with a single row.")

        logger.info(f"--- Generating ASYNC Forecast Report for Ticker: {ticker} (Sector: {sector}) ---")

        tasks_to_run_config = self._get_tasks_config()
        
        # 1. Tạo một danh sách các "công việc" (coroutines) cần chạy
        coroutines_to_run = [
            self._process_single_task(
                model_template, 
                task_template, 
                problem_id,
                sector,
                latest_enriched_data
            )
            for model_template, task_template, problem_id in tasks_to_run_config
        ]

        # 2. Sử dụng asyncio.gather để chạy tất cả các công việc song song
        logger.info(f"Dispatching {len(coroutines_to_run)} forecast tasks to run in parallel...")
        task_reports_list = await asyncio.gather(*coroutines_to_run)
        
        # 3. Tạo báo cáo cuối cùng từ kết quả đã thu thập
        final_report = ForecastingReport(
            ticker=ticker.upper(),
            sector=sector,
            forecasts=task_reports_list
            # Bạn có thể thêm timestamp ở đây nếu muốn
        )
        
        logger.info(f"--- Completed ASYNC Forecast Report for Ticker: {ticker} ---")
        return final_report
    
    async def _process_single_history_request(self, loaded_snapshot_model_wrapper: ForecastingModel,
                                           explainer: SHAPExplainer,
                                           snapshot_id: str,
                                           latest_enriched_data: pd.DataFrame):
        task = loaded_snapshot_model_wrapper.task
        X_instance = latest_enriched_data[task.selected_features]
            
        loop = asyncio.get_running_loop()
        predict_func = partial(loaded_snapshot_model_wrapper.predict, X_instance, snapshot_id)
        explain_func = partial(explainer.explain_prediction, X_instance)
        
        prediction_array, explanations = await asyncio.gather(
            loop.run_in_executor(None, predict_func),
            loop.run_in_executor(None, explain_func)
        )
        
        # 3. Đóng gói kết quả (chạy rất nhanh)
        task_report = SingleTaskForecastReport(
            task_name=task.task_id,
            task_metadata=task.get_metadata_for_plain(),
            prediction=prediction_array.flatten().tolist(),
            units=task.target_units,
            evidence=explanations
        )
        return task_report
    
    async def get_history_reports(
        self,
        latest_enriched_datas: pd.DataFrame,
        ticker: str,
        sector: str
    ) -> List[ForecastingReport]:
        """
        Tạo báo cáo dự báo cho một DataFrame LỚN chứa nhiều mốc thời gian lịch sử.
        Tối ưu hóa bằng cách nhóm các hàng theo snapshot_id để tái sử dụng SHAP explainer.
        """
        if latest_enriched_datas.empty:
            return []

        # Sắp xếp index để đảm bảo thứ tự thời gian
        latest_enriched_datas = latest_enriched_datas.sort_index(ascending=True)
        # 1. Chuẩn bị cấu trúc dữ liệu để lưu kết quả cuối cùng
        # Tạo một dict với key là timestamp và value là một ForecastingReport rỗng
        reports_by_date: Dict[pd.Timestamp, ForecastingReport] = {
            ts: ForecastingReport(ticker=ticker, sector=sector, forecasts=[])
            for ts in latest_enriched_datas.index
        }

        # 2. Lặp qua từng TASK (TripleBarrier, 5D-Dist, etc.)
        tasks_to_run_config = self._get_tasks_config()
        for model_template, task_template, problem_id in tasks_to_run_config:
            task_id = cfg.TASK_ID_SECTOR_TEMPLATE.format(problem=problem_id, sector=sector)
            
            # Tải model wrapper (chứa metadata và các con trỏ snapshot)
            model_wrapper = await self._get_or_load_model(model_template, task_template, task_id)    
            
            # Tải tất cả các model snapshot vật lý vào bộ nhớ nếu chưa có
            if not model_wrapper.snapshot_models:
                logger.info(f"  [History] Loading all snapshots for task '{task_id}'...")
                model_wrapper.load_all_snapshot_from_disk()

            # 3. Tối ưu hóa: Gán snapshot_id cho mỗi hàng TRƯỚC KHI xử lý
            df_with_snapshots = latest_enriched_datas.copy()
            
            # Sử dụng hàm get_snapshot_by_test_time để map mỗi timestamp tới snapshot_id tương ứng
            test_times_idx = pd.to_datetime(df_with_snapshots.index)
            snapshot_ids = np.array([model_wrapper.get_snapshot_by_test_time(test_time.to_pydatetime(), 'last') for test_time in test_times_idx])
            df_with_snapshots['snapshot_id'] = snapshot_ids

            # 4. Tối ưu hóa: Nhóm các hàng theo snapshot_id
            logger.info(f"  [History] Grouping {len(df_with_snapshots)} rows by snapshot_id for task '{task_id}'...")
            for snapshot_id, group_df in df_with_snapshots.groupby('snapshot_id'):
                snapshot_id = str(snapshot_id)
                logger.info(f"    - Processing group for snapshot '{snapshot_id}' ({len(group_df)} rows)...")
                # 5. Tạo Explainer MỘT LẦN cho cả nhóm
                
                # Tạo explainer chỉ một lần!
                explainer = self._create_explainer_sync(model_wrapper, snapshot_id)
                
                # 6. Xử lý từng hàng trong nhóm bằng explainer đã được tái sử dụng
                for index in group_df.index:
                    single_row_df = group_df.loc[[index]]

                    # Gọi worker để xử lý
                    single_task_report = await self._process_single_history_request(
                        loaded_snapshot_model_wrapper=model_wrapper, # Dùng model wrapper chính
                        explainer=explainer,         # Dùng explainer đã tái sử dụng
                        snapshot_id=snapshot_id,     # ID của snapshot hiện tại
                        latest_enriched_data=single_row_df
                    )
                    
                    # Thêm kết quả của task này vào ForecastingReport của ngày tương ứng
                    reports_by_date[index].forecasts.append(single_task_report)

            # (Tùy chọn) Giải phóng bộ nhớ của các snapshot sau khi xong một task lớn
            model_wrapper.clear_all_snapshot()

        # 7. Trả về danh sách các ForecastingReport đã được điền đầy đủ
        return list(reports_by_date.values())
    
    async def _preload_for_single_sector(self, sector_code: str):
        """Worker: Thực hiện toàn bộ quy trình preload cho một sector duy nhất."""
        logger.info(f"  - Pre-warming for sector: {sector_code}")
        try:
            tasks_to_run_config = self._get_tasks_config()
            
            for model_template, task_template, problem_id in tasks_to_run_config:
                task_id = cfg.TASK_ID_SECTOR_TEMPLATE.format(problem=problem_id, sector=sector_code)
                
                # 1. Tải model (tuần tự)
                model_wrapper = await self._get_or_load_model(model_template, task_template, task_id)
                
                # 2. Tạo explainer (tuần tự, sau khi có model)
                await self._get_or_create_explainer(model_wrapper)
                
                # SỬA LỖI QUAN TRỌNG: Dùng asyncio.sleep
                # Nhường CPU cho các coroutine khác, ví dụ một sector khác đang tải model
                await asyncio.sleep(0.5) # Có thể giảm thời gian sleep
                
        except Exception as e:
            # Ghi log lỗi cho sector cụ thể này mà không làm dừng toàn bộ quá trình
            logger.err(f"  - ERROR pre-warming for sector {sector_code}: {e}")
            raise PreloadCacheError('Forecasting Orchestrator',
                                    ['Model', 'Explainer'])
    
    async def preload_caches_for_all_sectors(self, sectors: List[str]):
        """
        Tải trước TẤT CẢ các model và explainer bằng cách chạy song song
        quy trình của từng sector.
        """
        logger.info("--- FORECASTING: Starting PARALLEL pre-warming process for all models & explainers ---")
        
        if not sectors:
            logger.warn("No sectors provided for pre-warming.")
            return

        logger.info(f"Found {len(sectors)} sectors to pre-warm: {sectors}")

        # 1. Tạo một danh sách các "công việc" (coroutines) cần thực hiện
        # Mỗi công việc là một lần gọi đến worker cho một sector
        tasks = [self._preload_for_single_sector(sector_code) for sector_code in sectors]

        # 2. Sử dụng asyncio.gather để chạy tất cả các công việc song song
        # gather sẽ chờ cho đến khi tất cả các tác vụ trong danh sách hoàn thành.
        await asyncio.gather(*tasks)
        
        logger.info("--- FORECASTING: Pre-warming process complete ---")
    
    def _get_tasks_config(self):
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