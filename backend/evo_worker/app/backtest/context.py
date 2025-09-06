"""Backtest context management for handling the lifecycle of backtest data for individual tickers."""

import asyncio
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional

from app.core.exceptions import BacktestError
import app.core.config as cfg

from .data_prepare import BacktestDataPreparer
from .selector import BacktestPointSelector
from . import api_caller

from itapia_common.logger import ITAPIALogger
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from itapia_common.schemas.entities.backtest import BACKTEST_CONTEXT_STATUS

logger = ITAPIALogger('Backtest Context')


class BacktestContext:
    """Manage the complete lifecycle of backtest data for a single ticker.
    
    Includes selecting dates, requesting report generation, waiting for completion,
    and loading final data into memory.
    """

    def __init__(self, ticker: str, data_preparer: BacktestDataPreparer,
                 selector: BacktestPointSelector,
                 is_ready: bool = False):
        """Initialize backtest context for a ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            data_preparer (BacktestDataPreparer): Data preparer instance
            selector (BacktestPointSelector): Point selector instance
            is_ready (bool, optional): Whether context is pre-loaded. Defaults to False
        """
        self.ticker = ticker
        self.data_preparer = data_preparer
        self.selector = selector
        
        self.job_id: Optional[str] = None  # Job ID for data generation task

        # Data will be loaded here
        self.ohlcv_df: Optional[pd.DataFrame] = None
        self.historical_reports: List[QuickCheckAnalysisReport] = []

        # Status management variables
        self.status: BACKTEST_CONTEXT_STATUS = 'IDLE'
        self.data_ready_event = asyncio.Event()
        
        if is_ready:
            self.status = 'READY_LOAD'
            self.data_ready_event.set()

    async def prepare_data_async(self) -> None:
        """Main coordinator function: Trigger the complete data preparation process.
        
        This is the sole entry point from outside.
        """
        if self.status != 'IDLE':
            logger.warn(f"Preparation for ticker {self.ticker} already started. Current status: {self.status}")
            return
            
        logger.info(f"Starting data preparation for ticker: {self.ticker}")
        self.status = 'PREPARING'
        
        try:
            # 1. Get raw OHLCV data
            self.ohlcv_df = self.data_preparer.get_daily_ohlcv_for_ticker(self.ticker, limit=5000)
            if self.ohlcv_df.empty:
                raise ValueError("Failed to fetch OHLCV data.")

            # 2. Select backtest points
            
            timestamps_to_request = self.selector.get_points_as_timestamps()
            
            if not timestamps_to_request:
                logger.warn(f"No backtest points selected for ticker {self.ticker}. Marking as ready.")
                self.status = 'READY_LOAD'
                self.data_ready_event.set()
                return

            # 3. Send request to generate reports to AI Service Quick
            response = await api_caller.trigger_backtest_generation_task(
                ticker=self.ticker,
                timestamps=timestamps_to_request,
            )
            self.job_id = response.job_id
            
            # 4. Start polling loop to wait for completion
            await self._poll_for_completion()

        except Exception as e:
            logger.err(f"Failed to prepare data for {self.ticker}: {e}")
            self.status = 'FAILED'
            # Still set event so anyone waiting won't hang, but they'll see status is FAILED
            self.data_ready_event.set()

    async def _poll_for_completion(self) -> None:
        """Asynchronous polling loop to check status of data generation task."""
        if not self.job_id:
            raise BacktestError(msg='Cannot poll for completion without a job_id.')
        
        polling_interval = cfg.POLLING_INTERVAL_SECONDS
        logger.info(f"Polling for backtest generation status every {polling_interval} seconds...")
        
        while True:
            try:
                response = await api_caller.check_backtest_generation_status(self.job_id)
                logger.info(f"Current backtest generation of job {self.job_id} status: {response.status}")
                
                if response.status == 'COMPLETED':
                    logger.info("Task completed. Loading reports from database...")
                    #await self._load_reports_from_db()
                    self.status = 'READY_LOAD'
                    self.data_ready_event.set()
                    break  # Exit loop
                
                elif response.status == 'FAILED':
                    logger.err("Backtest generation task failed on AI Service Quick.")
                    self.status = 'FAILED'
                    self.data_ready_event.set()
                    break  # Exit loop
                    
                # If still 'RUNNING' or 'IDLE', wait and try again
                await asyncio.sleep(polling_interval)
                
            except Exception as e:
                logger.err(f"Error during polling for {self.ticker}: {e}")
                self.status = 'FAILED'
                self.data_ready_event.set()
                break
            
    def _choose_reports_from_selector(self, reports: List[QuickCheckAnalysisReport]) -> List[QuickCheckAnalysisReport]:
        """Select reports based on selector criteria.
        """
        if not reports:
            return []
        
        report_dates = pd.to_datetime([r.generated_timestamp for r in reports], unit='s', utc=True)
        target_dates = pd.to_datetime(self.selector.get_points_as_timestamps(), unit="s", utc=True)
        
        report_series = pd.Series(range(len(reports)), index=report_dates)
        report_indices = report_dates.get_indexer(target_dates, method='nearest', tolerance=pd.Timedelta(timedelta(days=3)))
        
        valid_indices = set(idx for idx in report_indices if idx != -1)
        
        return [reports[i] for i in sorted(list(valid_indices))]

    async def load_data_into_memory(self, max_reports: Optional[int] = None) -> None:
        """Load all required data (OHLCV and reports) into RAM.
        
        This is an async function.
        
        Args:
            max_reports (Optional[int], optional): Maximum number of reports to load. 
                Defaults to None (no limit).
        """
        
        await self.data_ready_event.wait()
        if self.status not in ['READY_LOAD', 'READY_SERVE']:
            raise BacktestError(f"Data is not available to load for ticker {self.ticker}. Status: {self.status}")

        logger.info(f"Lazy loading data for ticker: {self.ticker}")
        loop = asyncio.get_running_loop()

        # Load OHLCV and Reports in parallel
        ohlcv_task = loop.run_in_executor(None, self.data_preparer.get_daily_ohlcv_for_ticker, self.ticker, 5000)
        reports_task = loop.run_in_executor(None, self.data_preparer.get_backtest_reports_for_ticker, self.ticker)
        
        self.ohlcv_df, historical_reports = await asyncio.gather(ohlcv_task, reports_task)
        
        relevant_reports = self._choose_reports_from_selector(historical_reports)
        relevant_reports.sort(key=lambda x: x.generated_timestamp, reverse=True)
        
        if max_reports is not None and len(relevant_reports) > max_reports:
            relevant_reports = relevant_reports[:max_reports]
        
        self.historical_reports = relevant_reports

        logger.info(f"Successfully loaded {len(self.historical_reports)} reports and OHLCV data for {self.ticker}.")
        self.status = 'READY_SERVE'  # Final state: data resides in RAM

    def clear_data_from_memory(self) -> None:
        """Clear heavy data from memory to free up RAM."""
        logger.info(f"Clearing in-memory data for ticker: {self.ticker}")
        self.historical_reports = []
        self.ohlcv_df = None
        if self.status == 'READY_SERVE':
            self.status = 'READY_LOAD'
    

class BacktestContextManager:
    """Manager that coordinates backtest data preparation, running in parallel
    with a limited number to avoid overloading AI Service Quick.
    """
    
    def __init__(self, data_preparer: BacktestDataPreparer):
        """Initialize backtest context manager.
        
        Args:
            data_preparer (BacktestDataPreparer): Data preparer instance
        """
        self.data_preparer = data_preparer
        self.contexts: Dict[str, BacktestContext] = {}
        self.selector: Dict[str, BacktestPointSelector] = {}
        
    def get_all_ticker_contexts(self) -> List[str]:
        """Get all ticker symbols with contexts.
        
        Returns:
            List[str]: List of all ticker symbols
        """
        return self.data_preparer.get_all_tickers()
        
    def add_context(self, ticker: str, selector: BacktestPointSelector) -> None:
        """Add a context for a specific ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            selector (BacktestPointSelector): Point selector for the ticker
        """
        context = BacktestContext(
            ticker=ticker,
            data_preparer=self.data_preparer,
            is_ready=True,
            selector=selector
        )
        self.contexts[ticker] = context
        self.selector[ticker] = selector

    async def _prepare_single_context(self, ticker: str, semaphore: asyncio.Semaphore) -> None:
        """Worker function: Execute complete process for a single ticker,
        controlled by a semaphore.
        
        Args:
            ticker (str): Stock ticker symbol
            semaphore (asyncio.Semaphore): Semaphore controlling concurrency
        """
        async with semaphore:  # Wait for an available "slot"
            logger.info(f"Starting preparation for ticker: {ticker}...")
            context = BacktestContext(
                ticker=ticker,
                data_preparer=self.data_preparer,
                selector=self.selector[ticker]
            )
            self.contexts[ticker] = context
            # prepare_data_async will now send requests for 1 ticker
            # and poll until completion
            await context.prepare_data_async() 

    async def prepare_all_contexts(self) -> None:
        """Initialize and run data preparation process for all tickers in parallel,
        with concurrency limits.
        """
        # Limit to running 5 tickers at once to avoid overloading AI Quick
        concurrency_limit = cfg.PARALLEL_CONCURRENCY_LIMIT
        semaphore = asyncio.Semaphore(concurrency_limit)
        tickers = self.data_preparer.get_all_tickers()
        #tickers = ['AAPL', 'NVDA']
        
        logger.info(f"Preparing backtest contexts for {len(tickers)} tickers with a concurrency limit of {concurrency_limit}...")
        
        tasks = [self._prepare_single_context(ticker, semaphore) for ticker in tickers]
        
        await asyncio.gather(*tasks)
        
        logger.info("Finished preparation for all tickers.")
        self.log_summary()
        
    def get_context(self, ticker: str) -> Optional[BacktestContext]:
        """Get prepared context for a specific ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            Optional[BacktestContext]: Prepared context or None if not found
        """
        return self.contexts.get(ticker)

    def get_ready_contexts(self) -> List[BacktestContext]:
        """Return a list of all contexts in 'READY_SERVE' state.
        
        This is the list that FitnessEvaluator will work with.
        
        Returns:
            List[BacktestContext]: List of ready contexts
        """
        return [ctx for ctx in self.contexts.values() if ctx.status == 'READY_SERVE']

    def log_summary(self) -> None:
        """Log summary of all context statuses."""
        total = len(self.contexts)
        ready_count = len([ctx for ctx in self.contexts.values() if ctx.status == 'READY_LOAD'])
        failed_count = len([ctx for ctx in self.contexts.values() if ctx.status == 'FAILED'])
        preparing_count = len([ctx for ctx in self.contexts.values() if ctx.status == 'PREPARING'])
        
        logger.info("--- Backtest Context Manager Summary ---")
        logger.info(f"Total Tickers: {total}")
        logger.info(f"  - Ready: {ready_count}")
        logger.info(f"  - Failed: {failed_count}")
        logger.info(f"  - Still Preparing: {preparing_count}")
        logger.info("------------------------------------")