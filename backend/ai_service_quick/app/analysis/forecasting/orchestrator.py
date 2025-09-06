"""Forecasting orchestrator for coordinating prediction and explanation processes."""

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

# Temporary cache


class ForecastingOrchestrator:
    """Orchestrates the forecasting and explanation process for a single stock."""
    
    def __init__(self):
        """Initialize the forecasting orchestrator with model and explainer caches."""
        self.model_cache = AsyncInMemoryCache()
        self.explainer_cache = AsyncInMemoryCache()

    async def _get_or_load_model(self, model_template: ForecastingModel, 
                          task_template: AvailableTaskTemplate, 
                          task_id: str) -> ForecastingModel:
        """Get model from cache. If not available, load from Kaggle and cache it.
        
        This function automatically "revives" the Task from saved metadata.
        
        Args:
            model_template (ForecastingModel): Model template to use
            task_template (AvailableTaskTemplate): Task template to use
            task_id (str): Unique task identifier
            
        Returns:
            ForecastingModel: Loaded forecasting model
        """
        model_slug = model_template.get_model_slug(task_id=task_id)

        async def model_factory():
            logger.info(f"CACHE MISS: Loading model for task '{task_id}'...")
            
            # Run blocking function in executor
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, 
                model_template.load_model_from_kaggle, # Blocking function
                cfg.KAGGLE_USERNAME, task_template, task_id # Parameters
            )
            return model_template

        return await self.model_cache.get_or_set_with_lock(model_slug, model_factory)
    
    async def _get_or_create_explainer(self, model_wrapper: ForecastingModel, snapshot_id: str|None=None) -> SHAPExplainer:
        """Get explainer from cache. If not available, create and cache it.
        
        Args:
            model_wrapper (ForecastingModel): Model wrapper containing the task
            snapshot_id (str | None, optional): Snapshot identifier. Defaults to None.
            
        Returns:
            SHAPExplainer: Created or cached explainer
        """
        task = model_wrapper.task
        # Use task_id as key because explainer depends on task type
        explainer_key = task.task_id

        async def explainer_factory():
            # Creating explainer is CPU-bound, can run in executor
            logger.info('CACHE MISS for Explainer')
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._create_explainer_sync, model_wrapper, snapshot_id)
        
        return await self.explainer_cache.get_or_set_with_lock(explainer_key, explainer_factory)
    
    def _create_explainer_sync(self, model_wrapper: ForecastingModel, snapshot_id: str|None = None) -> SHAPExplainer:
        """Create explainer synchronously based on task type.
        
        Args:
            model_wrapper (ForecastingModel): Model wrapper containing the task
            snapshot_id (str | None, optional): Snapshot identifier. Defaults to None.
            
        Returns:
            SHAPExplainer: Created explainer
        """
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
        """Worker coroutine: Process a single forecasting task completely asynchronously.
        
        Args:
            model_template (ForecastingModel): Model template to use
            task_template (AvailableTaskTemplate): Task template to use
            problem_id (str): Problem identifier
            sector_code (str): Sector code
            latest_enriched_data (pd.DataFrame): Latest enriched data for prediction
            
        Returns:
            SingleTaskForecastReport: Forecast report for this task
        """
        task_id = cfg.TASK_ID_SECTOR_TEMPLATE.format(problem=problem_id, sector=sector_code)
        
        # 1. Get model and explainer (already async, very good)
        model_wrapper = await self._get_or_load_model(model_template, task_template, task_id)
        explainer = await self._get_or_create_explainer(model_wrapper)
        
        task = model_wrapper.task
        X_instance = latest_enriched_data[task.selected_features]
        
        loop = asyncio.get_running_loop()

        # 2. Run CPU-bound tasks in parallel in executor
        #    (Since predict and explain are usually independent, they can run simultaneously)
        logger.info(f"  - Running predict & explain for task: {task_id}")
        
        # Use functools.partial to wrap functions with parameters
        predict_func = partial(model_wrapper.predict, X_instance)
        explain_func = partial(explainer.explain_prediction, X_instance)

        prediction_array, explanations = await asyncio.gather(
            loop.run_in_executor(None, predict_func),
            loop.run_in_executor(None, explain_func)
        )
        
        # 3. Package results (runs very fast)
        task_report = SingleTaskForecastReport(
            task_name=task.task_id,
            task_metadata=task.get_metadata_for_plain(),
            prediction=prediction_array.flatten().tolist(),
            units=task.target_units,
            evidence=explanations
        )
        logger.info(f"  - Completed task: {task_id}")
        return task_report
        
    async def generate_report(self, latest_enriched_data: pd.DataFrame, ticker: str, sector: str) -> ForecastingReport:
        """Main async function: Generate a complete forecast report by running
        different analysis tasks in parallel.
        
        Args:
            latest_enriched_data (pd.DataFrame): Latest enriched data for prediction
            ticker (str): Stock ticker symbol
            sector (str): Sector code
            
        Returns:
            ForecastingReport: Complete forecasting report
            
        Raises:
            ValueError: If input is not a DataFrame with a single row
        """
        if not isinstance(latest_enriched_data, pd.DataFrame) or len(latest_enriched_data) != 1:
            raise ValueError("Input must be a DataFrame with a single row.")

        logger.info(f"--- Generating ASYNC Forecast Report for Ticker: {ticker} (Sector: {sector}) ---")

        tasks_to_run_config = self._get_tasks_config()
        
        # 1. Create a list of "jobs" (coroutines) to run
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

        # 2. Use asyncio.gather to run all jobs in parallel
        logger.info(f"Dispatching {len(coroutines_to_run)} forecast tasks to run in parallel...")
        task_reports_list = await asyncio.gather(*coroutines_to_run)
        
        # 3. Create final report from collected results
        final_report = ForecastingReport(
            ticker=ticker.upper(),
            sector=sector,
            forecasts=task_reports_list
            # You can add timestamp here if needed
        )
        
        logger.info(f"--- Completed ASYNC Forecast Report for Ticker: {ticker} ---")
        return final_report
    
    async def _process_single_history_request(self, loaded_snapshot_model_wrapper: ForecastingModel,
                                           explainer: SHAPExplainer,
                                           snapshot_id: str,
                                           latest_enriched_data: pd.DataFrame) -> SingleTaskForecastReport:
        """Process a single history request.
        
        Args:
            loaded_snapshot_model_wrapper (ForecastingModel): Loaded model wrapper
            explainer (SHAPExplainer): Explainer to use
            snapshot_id (str): Snapshot identifier
            latest_enriched_data (pd.DataFrame): Latest enriched data
            
        Returns:
            SingleTaskForecastReport: Forecast report for this task
        """
        task = loaded_snapshot_model_wrapper.task
        X_instance = latest_enriched_data[task.selected_features]
            
        loop = asyncio.get_running_loop()
        predict_func = partial(loaded_snapshot_model_wrapper.predict, X_instance, snapshot_id)
        explain_func = partial(explainer.explain_prediction, X_instance)
        
        prediction_array, explanations = await asyncio.gather(
            loop.run_in_executor(None, predict_func),
            loop.run_in_executor(None, explain_func)
        )
        
        # 3. Package results (runs very fast)
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
        """Generate forecast reports for a LARGE DataFrame containing multiple historical time points.
        
        Optimized by grouping rows by snapshot_id to reuse SHAP explainer.
        
        Args:
            latest_enriched_datas (pd.DataFrame): DataFrame with multiple historical timestamps
            ticker (str): Stock ticker symbol
            sector (str): Sector code
            
        Returns:
            List[ForecastingReport]: List of forecasting reports for each timestamp
        """
        if latest_enriched_datas.empty:
            return []

        # Sort index to ensure chronological order
        latest_enriched_datas = latest_enriched_datas.sort_index(ascending=True)
        # 1. Prepare data structure to store final results
        # Create a dict with timestamp as key and empty ForecastingReport as value
        reports_by_date: Dict[pd.Timestamp, ForecastingReport] = {
            ts: ForecastingReport(ticker=ticker, sector=sector, forecasts=[])
            for ts in latest_enriched_datas.index
        }

        # 2. Loop through each TASK (TripleBarrier, 5D-Dist, etc.)
        tasks_to_run_config = self._get_tasks_config()
        for model_template, task_template, problem_id in tasks_to_run_config:
            task_id = cfg.TASK_ID_SECTOR_TEMPLATE.format(problem=problem_id, sector=sector)
            
            # Load model wrapper (contains metadata and snapshot pointers)
            model_wrapper = await self._get_or_load_model(model_template, task_template, task_id)    
            
            # Load all physical model snapshots into memory if not already loaded
            if not model_wrapper.snapshot_models:
                logger.info(f"  [History] Loading all snapshots for task '{task_id}'...")
                model_wrapper.load_all_snapshot_from_disk()

            # 3. Optimization: Assign snapshot_id to each row BEFORE processing
            df_with_snapshots = latest_enriched_datas.copy()
            
            # Use get_snapshot_by_test_time function to map each timestamp to corresponding snapshot_id
            test_times_idx = pd.to_datetime(df_with_snapshots.index)
            snapshot_ids = np.array([model_wrapper.get_snapshot_by_test_time(test_time.to_pydatetime(), 'last') for test_time in test_times_idx])
            df_with_snapshots['snapshot_id'] = snapshot_ids

            # 4. Optimization: Group rows by snapshot_id
            logger.info(f"  [History] Grouping {len(df_with_snapshots)} rows by snapshot_id for task '{task_id}'...")
            for snapshot_id, group_df in df_with_snapshots.groupby('snapshot_id'):
                snapshot_id = str(snapshot_id)
                logger.info(f"    - Processing group for snapshot '{snapshot_id}' ({len(group_df)} rows)...")
                # 5. Create Explainer ONCE for the entire group
                
                # Create explainer only once!
                explainer = self._create_explainer_sync(model_wrapper, snapshot_id)
                
                # 6. Process each row in the group using the reused explainer
                for index in group_df.index:
                    single_row_df = group_df.loc[[index]]

                    # Call worker to process
                    single_task_report = await self._process_single_history_request(
                        loaded_snapshot_model_wrapper=model_wrapper, # Use main model wrapper
                        explainer=explainer,         # Use reused explainer
                        snapshot_id=snapshot_id,     # Current snapshot ID
                        latest_enriched_data=single_row_df
                    )
                    
                    # Add this task's result to the ForecastingReport of the corresponding date
                    reports_by_date[index].forecasts.append(single_task_report)

            # (Optional) Free memory of snapshots after completing a large task
            model_wrapper.clear_all_snapshot()

        # 7. Return list of fully populated ForecastingReports
        return list(reports_by_date.values())
    
    async def _preload_for_single_sector(self, sector_code: str):
        """Worker: Perform complete preload process for a single sector.
        
        Args:
            sector_code (str): Sector code to preload
            
        Raises:
            PreloadCacheError: If preloading fails for this sector
        """
        logger.info(f"  - Pre-warming for sector: {sector_code}")
        try:
            tasks_to_run_config = self._get_tasks_config()
            
            for model_template, task_template, problem_id in tasks_to_run_config:
                task_id = cfg.TASK_ID_SECTOR_TEMPLATE.format(problem=problem_id, sector=sector_code)
                
                # 1. Load model (sequential)
                model_wrapper = await self._get_or_load_model(model_template, task_template, task_id)
                
                # 2. Create explainer (sequential, after model is available)
                await self._get_or_create_explainer(model_wrapper)
                
                # IMPORTANT FIX: Use asyncio.sleep
                # Yield CPU to other coroutines, e.g., another sector loading model
                await asyncio.sleep(0.5) # Can reduce sleep time
                
        except Exception as e:
            # Log error for this specific sector without stopping the entire process
            logger.err(f"  - ERROR pre-warming for sector {sector_code}: {e}")
            raise PreloadCacheError('Forecasting Orchestrator',
                                    ['Model', 'Explainer'])
    
    async def preload_caches_for_all_sectors(self, sectors: List[str]):
        """Preload ALL models and explainers by running each sector's process in parallel.
        
        Args:
            sectors (List[str]): List of sector codes to preload
        """
        logger.info("--- FORECASTING: Starting PARALLEL pre-warming process for all models & explainers ---")
        
        if not sectors:
            logger.warn("No sectors provided for pre-warming.")
            return

        logger.info(f"Found {len(sectors)} sectors to pre-warm: {sectors}")

        # 1. Create a list of "jobs" (coroutines) to execute
        # Each job is a call to the worker for a sector
        tasks = [self._preload_for_single_sector(sector_code) for sector_code in sectors]

        # 2. Use asyncio.gather to run all jobs in parallel
        # gather will wait until all tasks in the list complete.
        await asyncio.gather(*tasks)
        
        logger.info("--- FORECASTING: Pre-warming process complete ---")
    
    def _get_tasks_config(self) -> List[tuple]:
        """Private function to centralize task definition.
        
        Avoids code duplication between generate_report and preload_caches.
        
        Returns:
            List[tuple]: Configuration of (Model Template, Task Template, Problem ID) tuples
        """

        # Return configuration of (Model Template, Task Template, Problem ID) pairs
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