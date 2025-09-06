"""Analysis orchestrator for coordinating all quick check analysis modules."""

import asyncio
import time
from datetime import datetime, timezone
from typing import Literal, Union
import numpy as np
import pandas as pd
from .data_prepare.orchestrator import DataPrepareOrchestrator
from .technical.orchestrator import TechnicalOrchestrator
from .forecasting.orchestrator import ForecastingOrchestrator
from .news.orchestrator import NewsOrchestrator
from .backtest.orchestrator import BacktestOrchestrator
from .explainer.orchestrator import AnalysisExplainerOrchestrator, ExplainReportType

from app.core.exceptions import PreloadCacheError, NoDataError, NotReadyServiceError, MissingReportError

from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from itapia_common.schemas.entities.analysis.forecasting import ForecastingReport
from itapia_common.schemas.entities.analysis.news import NewsAnalysisReport
from itapia_common.schemas.entities.analysis.technical import TechnicalReport
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Analysis Orchestrator')


def clean_json_outliers(obj) -> dict:
    """Recursively scan through an object (dict, list) and replace special 
    numpy/float values (inf, -inf, nan) with None.
    
    Args:
        obj: Object to clean (dict, list, or numeric value)
        
    Returns:
        dict: Cleaned object with special values replaced by None
    """
    if isinstance(obj, dict):
        return {k: clean_json_outliers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_outliers(elem) for elem in obj]
    elif isinstance(obj, (np.integer, np.floating, float)):
        # Check if it's nan, inf, or -inf
        if not np.isfinite(obj):
            return None  # Replace with None (will become null in JSON)
    return obj


class AnalysisOrchestrator:
    """Super Orchestrator ("CEO") for the entire Quick Check Analysis process (async version).
    
    It coordinates the orchestrators of each major module to execute complete 
    business processes.
    """
    
    def __init__(self, data_preparer: DataPrepareOrchestrator,
                 tech_analyzer: TechnicalOrchestrator,
                 forecaster: ForecastingOrchestrator,
                 news_analyzer: NewsOrchestrator,
                 explainer: AnalysisExplainerOrchestrator,
                 backtest_orchestrator: BacktestOrchestrator):
        """Initialize the AnalysisOrchestrator with all required sub-orchestrators.
        
        Args:
            data_preparer (DataPrepareOrchestrator): Data preparation orchestrator
            tech_analyzer (TechnicalOrchestrator): Technical analysis orchestrator
            forecaster (ForecastingOrchestrator): Forecasting orchestrator
            news_analyzer (NewsOrchestrator): News analysis orchestrator
            explainer (AnalysisExplainerOrchestrator): Analysis explainer orchestrator
            backtest_orchestrator (BacktestOrchestrator): Backtest orchestrator
        """
        # Initialize department heads
        self.data_preparer = data_preparer
        self.tech_analyzer = tech_analyzer
        self.forecaster = forecaster
        self.news_analyzer = news_analyzer
        self.explainer = explainer
        self.backtest_generator = backtest_orchestrator
        self.is_active = False
        
    def get_all_tickers(self) -> list:
        """Get all available tickers.
        
        Returns:
            list: List of all available tickers
        """
        return self.data_preparer.get_all_tickers()

    # === ASYNC HELPER METHODS FOR EACH MODULE ===

    def _prepare_and_run_technical_analysis(self, enriched_daily_df: pd.DataFrame, 
                                            enriched_intraday_df: pd.DataFrame, 
                                            daily_analysis_type: str, required_type: str) -> TechnicalReport:
        """Technical Analysis Phase (synchronous because tasks are very fast).
        
        Args:
            enriched_daily_df (pd.DataFrame): Daily DataFrame with technical features
            enriched_intraday_df (pd.DataFrame): Intraday DataFrame with technical features
            daily_analysis_type (str): Type of daily analysis ('short', 'medium', 'long')
            required_type (str): Type of analysis required ('daily', 'intraday', 'all')
            
        Returns:
            TechnicalReport: Technical analysis report
        """
        logger.info("CEO -> TechAnalyzer: Performing technical analysis...")

        # This is a fast task, can run synchronously.
        return self.tech_analyzer.get_full_analysis(
            enriched_daily_df, 
            enriched_intraday_df,
            required_type=required_type,
            daily_analysis_type=daily_analysis_type
        )

    async def _prepare_and_run_forecasting(self, ticker: str, enriched_daily_df: pd.DataFrame) -> ForecastingReport:
        """Forecasting Phase (asynchronous).
        
        Args:
            ticker (str): Stock ticker symbol
            enriched_daily_df (pd.DataFrame): Daily DataFrame with technical features
            
        Returns:
            ForecastingReport: Forecasting analysis report
        """
        logger.info("CEO -> Forecaster: Preparing data and running forecast...")
        # 1. Prepare input data (fast, synchronous)
        sector = self.data_preparer.get_sector_code_of(ticker)
        latest_features = enriched_daily_df.iloc[-1:]

        # 2. Call generate_report function (heavy, asynchronous)
        return await self.forecaster.generate_report(latest_features, ticker, sector)

    async def _prepare_and_run_news_analysis(self, ticker: str) -> NewsAnalysisReport:
        """News Analysis Phase (asynchronous).
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            NewsAnalysisReport: News analysis report
        """
        logger.info("CEO -> NewsAnalyzer: Preparing data and running news analysis...")
        # 1. Prepare input data (fast, synchronous)
        news_texts = self.data_preparer.get_all_news_text_for_ticker(ticker)

        # 2. Call generate_report function (heavy, asynchronous)
        return await self.news_analyzer.generate_report(ticker, news_texts)
    
    def check_service_health(self) -> None:
        """Check if service is ready and active.
        
        Raises:
            NotReadyServiceError: If service is not ready
        """
        if not self.is_active:
            raise NotReadyServiceError('Service is not ready! Check after 5-10 minutes')
        
    def check_data_avaiable(self, ticker: str) -> None:
        """Check if data is available for a given ticker.
        
        Args:
            ticker (str): Stock ticker symbol to check
            
        Raises:
            NoDataError: If no data is found for the ticker
        """
        if not self.data_preparer.is_exist(ticker):
            raise NoDataError(f'Not found ticker {ticker}')

    # === MAIN COORDINATION FUNCTIONS (PROCESS 1) ===
    
    async def get_technical_report(self, ticker: str,
                                   daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                                   required_type: Literal['daily', 'intraday', 'all']='all'
                                   ) -> TechnicalReport:
        """Get technical analysis report for a specific ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            daily_analysis_type (Literal['short', 'medium', 'long'], optional): Type of daily analysis. 
                Defaults to 'medium'.
            required_type (Literal['daily', 'intraday', 'all'], optional): Type of analysis required. 
                Defaults to 'all'.
                
        Returns:
            TechnicalReport: Technical analysis report
            
        Raises:
            NotReadyServiceError: If service is not ready
            NoDataError: If no data is available for the ticker
        """
        self.check_service_health()
        self.check_data_avaiable(ticker)
        
        logger.info(f"--- CEO (ASYNC): Initiating TECHNICAL-ONLY analysis for '{ticker}' ---")
        
        # --- STEP 1: FETCH RAW DATA (SYNCHRONOUS) ---
        logger.info("CEO -> DataPreparer: Fetching price data...")
        daily_df = self.data_preparer.get_daily_ohlcv_for_ticker(ticker)
        intraday_df = self.data_preparer.get_intraday_ohlcv_for_ticker(ticker)

        if daily_df.empty: # Only need to check daily_df because forecasting and technical mainly rely on it
            logger.err(f"No daily data available for ticker {ticker}.")
            raise NoDataError(f"No daily data available for ticker {ticker}.")
        
        enriched_daily_df = self.tech_analyzer.get_daily_features(daily_df)
        enriched_intraday_df = self.tech_analyzer.get_intraday_features(intraday_df)
        
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(
            None, self._prepare_and_run_technical_analysis, 
            enriched_daily_df, enriched_intraday_df, daily_analysis_type, required_type
        )
        return report
    
    async def get_forecasting_report(self, ticker: str) -> ForecastingReport:
        """Get forecasting report for a specific ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            ForecastingReport: Forecasting analysis report
            
        Raises:
            NotReadyServiceError: If service is not ready
            NoDataError: If no data is available for the ticker
        """
        self.check_service_health()
        self.check_data_avaiable(ticker)
        
        logger.info(f"--- CEO (ASYNC): Initiating FORECASTING-ONLY analysis for '{ticker}' ---")
        
        # --- STEP 1: FETCH RAW DATA (SYNCHRONOUS) ---
        logger.info("CEO -> DataPreparer: Fetching price data...")
        daily_df = self.data_preparer.get_daily_ohlcv_for_ticker(ticker)

        if daily_df.empty: # Only need to check daily_df because forecasting and technical mainly rely on it
            logger.err(f"No daily data available for ticker {ticker}.")
            raise NoDataError(f"No daily data available for ticker {ticker}.")
        
        
        enriched_daily_df = self.tech_analyzer.get_daily_features(daily_df)
        return await self._prepare_and_run_forecasting(ticker, enriched_daily_df)
    
    async def get_news_report(self, ticker: str) -> NewsAnalysisReport:
        """Get news analysis report for a specific ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            NewsAnalysisReport: News analysis report
            
        Raises:
            NotReadyServiceError: If service is not ready
            NoDataError: If no data is available for the ticker
        """
        self.check_service_health()
        self.check_data_avaiable(ticker)
        
        logger.info(f"--- CEO: Initiating NEWS-ONLY analysis for '{ticker}' ---")
        
        return await self._prepare_and_run_news_analysis(ticker)

    async def get_full_analysis_report(self, ticker: str, 
                                       daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                                       required_type: Literal['daily', 'intraday', 'all']='all'
                                      ) -> QuickCheckAnalysisReport:
        """Create a complete A-Z analysis report for a ticker, running heavy modules in parallel.
        
        Args:
            ticker (str): Stock ticker symbol
            daily_analysis_type (Literal['short', 'medium', 'long'], optional): Type of daily analysis. 
                Defaults to 'medium'.
            required_type (Literal['daily', 'intraday', 'all'], optional): Type of analysis required. 
                Defaults to 'all'.
                
        Returns:
            QuickCheckAnalysisReport: Complete analysis report
            
        Raises:
            NotReadyServiceError: If service is not ready
            NoDataError: If no data is available for the ticker
            MissingReportError: If any analysis module fails
        """
        self.check_service_health()
        self.check_data_avaiable(ticker)
        
        logger.info(f"--- CEO (ASYNC): Initiating full analysis for ticker '{ticker}' ---")
        
        # --- STEP 1: FETCH RAW DATA (SYNCHRONOUS) ---
        logger.info("CEO -> DataPreparer: Fetching price data...")
        daily_df = self.data_preparer.get_daily_ohlcv_for_ticker(ticker)
        intraday_df = self.data_preparer.get_intraday_ohlcv_for_ticker(ticker)

        if daily_df.empty: # Only need to check daily_df because forecasting and technical mainly rely on it
            logger.err(f"No daily data available for ticker {ticker}.")
            raise NoDataError(f"No daily data available for ticker {ticker}.")
        
        enriched_daily_df = self.tech_analyzer.get_daily_features(daily_df)
        enriched_intraday_df = self.tech_analyzer.get_intraday_features(intraday_df)

        # --- STEP 2: RUN ALL MODULES IN PARALLEL ---
        logger.info("CEO: Dispatching all analysis modules to run in parallel...")
        
        # Run Technical Analysis (fast task) in executor to avoid blocking
        # Although fast, putting it in executor is the safest way to ensure non-blocking.
        loop = asyncio.get_running_loop()
        technical_task = loop.run_in_executor(
            None, self._prepare_and_run_technical_analysis, 
            enriched_daily_df, enriched_intraday_df, daily_analysis_type, required_type
        )

        # Create tasks for heavy modules
        forecasting_task = self._prepare_and_run_forecasting(ticker, enriched_daily_df)
        news_task = self._prepare_and_run_news_analysis(ticker)

        # Use gather to wait for all to complete
        results = await asyncio.gather(
            technical_task, 
            forecasting_task, 
            news_task,
            return_exceptions=True # Very important for error handling
        )

        # --- STEP 3: CHECK ERRORS AND CONSOLIDATE RESULTS ---
        
        # Unpack results
        technical_report, forecasting_report, news_report = results

        # Check if any modules failed
        if isinstance(technical_report, Exception):
            logger.err(f"Technical analysis failed for {ticker}: {technical_report}")
            raise MissingReportError(f"Technical analysis module failed.")
        if isinstance(forecasting_report, Exception):
            logger.err(f"Forecasting failed for {ticker}: {forecasting_report}")
            raise MissingReportError(f"Forecasting module failed.")
        if isinstance(news_report, Exception):
            logger.err(f"News analysis failed for {ticker}: {news_report}")
            raise MissingReportError(f"News analysis module failed.")

        # --- STEP 4: CREATE FINAL REPORT ---
        generate_time = datetime.now(tz=timezone.utc)
        final_report = QuickCheckAnalysisReport(
            ticker=ticker.upper(),
            generated_at_utc=generate_time.isoformat(),
            generated_timestamp=int(generate_time.timestamp()),
            technical_report=technical_report,
            forecasting_report=forecasting_report,
            news_report=news_report
        )
        
        logger.info(f"--- CEO (ASYNC): Full analysis for '{ticker}' complete. ---")
        
        # Clean up NaN/inf values before returning
        cleaned_report_dict = clean_json_outliers(final_report.model_dump())
        return QuickCheckAnalysisReport.model_validate(cleaned_report_dict)
    
    async def get_full_explaination_report(
        self, 
        ticker: str, 
        daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
        required_type: Literal['daily', 'intraday', 'all']='all',
        explain_type: ExplainReportType = 'all'
    ) -> str:
        """Reuse the full JSON report and create a plain-text summary.
        
        Args:
            ticker (str): Stock ticker symbol
            daily_analysis_type (Literal['short', 'medium', 'long'], optional): Type of daily analysis. 
                Defaults to 'medium'.
            required_type (Literal['daily', 'intraday', 'all'], optional): Type of analysis required. 
                Defaults to 'all'.
            explain_type (ExplainReportType, optional): Type of explanation to generate. 
                Defaults to 'all'.
                
        Returns:
            str: Plain-text explanation of the analysis report
        """
        logger.info(f"--- CEO: Initiating PLAIN-TEXT explanation for '{ticker}' ---")
        
        # STEP 1: Call the main function to get structured data
        json_report = await self.get_full_analysis_report(
            ticker, daily_analysis_type, required_type
        )

        # STEP 2: Call the Explainer Orchestrator to "translate" the report
        explanation_text = self.explainer.explain(
            report=json_report, 
            report_type=explain_type
        )
        
        return explanation_text
    
    async def preload_all_caches(self) -> None:
        """Activate parallel cache warming process for ALL sub-modules.
        
        Raises:
            Exception: If any module fails during pre-warming
        """
        logger.info("--- CEO: Starting PARALLEL pre-warming for all sub-modules ---")
        
        # Prepare required parameters
        sectors = self.data_preparer.get_all_sectors_code()
        #sectors = ['TECH']
        # 1. Create a list of "major tasks" to execute
        # Each task is a call to a department head's preload function
        tasks = [
            self.forecaster.preload_caches_for_all_sectors(sectors),
            self.news_analyzer.preload_caches()
            # In the future, other modules can be added here
            # self.another_module.preload()
        ]

        # 2. Use asyncio.gather to run all tasks in parallel and WAIT for them
        # IMPORTANT FIX: Add `await` at the front
        # Use return_exceptions=True so one module error doesn't crash the entire process
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # (Optional but recommended) Check results to log if there are errors
        module_names = ["News Analysis"]
        has_errors = False
        for result, name in zip(results, module_names):
            if isinstance(result, Exception):
                logger.err(f"  - Pre-warming FAILED for module '{name}': {result}")
                has_errors = True
            else:
                logger.info(f"  - Pre-warming complete for module '{name}'.")

        # 3. Only after ALL have completed, set status to active
        if not has_errors:
            self.is_active = True
            logger.info("--- CEO: All modules pre-warmed successfully. Service is now active. ---")
        else:
            logger.warn("--- CEO: Pre-warming process completed with errors. Service might not be fully functional. ---")
            
    def prepare_training_data_for_sector(self, sector_code: str) -> pd.DataFrame:
        """PROCESS 2: Prepare a large DataFrame ready for training,
        for all tickers in a sector group.
        
        Args:
            sector_code (str): Sector code to prepare training data for
            
        Returns:
            pd.DataFrame: DataFrame with training-ready data for the sector
        """
        logger.info(f"--- CEO: Preparing training data for sector '{sector_code}' ---")
        
        # STEP 1: FETCH AGGREGATED SECTOR DATA
        logger.info("CEO -> DataPreparer: Fetching and transforming sector data...")
        sector_ohlcv_df = self.data_preparer.get_daily_ohlcv_for_sector(sector_code)
        
        if sector_ohlcv_df.empty:
            logger.err(f"No data found for sector {sector_code}.")
            return pd.DataFrame()

        # STEP 2: CREATE FEATURES FOR AGGREGATED DATA
        # Note: Need to iterate through each ticker to create correct features
        logger.info("CEO -> TechAnalyzer: Generating features for sector data...")
        all_enriched_dfs = []
        for ticker, group_df in sector_ohlcv_df.groupby('ticker'):
            logger.info(f"  - Generating features for {ticker}...")
            enriched_ticker_df = self.tech_analyzer.get_daily_features(group_df)
            all_enriched_dfs.append(enriched_ticker_df)
        
        enriched_sector_df = pd.concat(all_enriched_dfs)

        # STEP 3 (FUTURE): CREATE TARGETS
        # training_ready_df = self.forecasting_pipeline.create_targets(enriched_sector_df)
        
        logger.info(f"--- CEO: Training data for '{sector_code}' is ready. ---")
        return enriched_sector_df # Temporarily return df with features
    
    def export_local_data_for_sector(self, sector_code: str) -> None:
        """Export local training data for a sector to CSV file.
        
        Args:
            sector_code (str): Sector code to export data for
        """
        df = self.prepare_training_data_for_sector(sector_code)
        df.to_csv(f'/ai-service-quick/local/training_{sector_code}.csv')
        
    # =================================================================
    # SECTION: BACKTESTING DATA GENERATION - REFACTORED
    # =================================================================

    async def _process_single_ticker_for_backtest(self, ticker: str, sector: str, backtest_dates: list[datetime]) -> None:
        """Helper function: Execute the entire backtest data creation process for a SINGLE ticker.
        
        Args:
            ticker (str): Stock ticker symbol to process
            sector (str): Sector code for the ticker
            backtest_dates (list[datetime]): List of dates to backtest
        """
        logger.info(f"  -> Processing Ticker: '{ticker}' for {len(backtest_dates)} dates")
        loop = asyncio.get_running_loop()

        # 1. Get historical data and backtest points
        full_daily_df = self.data_preparer.get_daily_ohlcv_for_ticker(ticker, limit=5000)
        if full_daily_df.empty:
            logger.warn(f"  No daily data for '{ticker}'. Skipping ticker.")
            return
        
        enriched_daily_df = self.tech_analyzer.get_daily_features(full_daily_df).copy()

        target_dates_ts = pd.to_datetime(backtest_dates, utc=True)
        target_dates_iloc = enriched_daily_df.index.get_indexer(target_dates_ts, method='ffill')
        
        valid_target_ilocs = target_dates_iloc[(target_dates_iloc != -1) & (target_dates_iloc > 0)]
        
        if len(valid_target_ilocs) == 0:
            logger.warn(f"  No valid historical data points for '{ticker}' that allow for i-1 slicing.")
            return

        forecasting_input_ilocs = valid_target_ilocs - 1
        
        selected_datas = enriched_daily_df.iloc[forecasting_input_ilocs].copy()

        if selected_datas.empty:
            logger.warn(f"  No valid historical data points for '{ticker}'. Skipping ticker.")
            return

        # 2. Run the heaviest module (Forecasting) once for all data points
        forecasting_reports = await self.forecaster.get_history_reports(
            latest_enriched_datas=selected_datas, ticker=ticker, sector=sector
        )
        if len(forecasting_reports) != len(selected_datas):
            logger.err(f"  Mismatch between selected data points ({len(selected_datas)}) and forecasts ({len(forecasting_reports)}). Skipping ticker.")
            return

        # 3. Prepare Technical and News tasks to run in parallel
        tasks_to_gather = []
        for iloc_pos in valid_target_ilocs:
            # Prepare data slice for technical
            historical_slice_df = enriched_daily_df.iloc[:iloc_pos]
            current_date_ohlcv = enriched_daily_df.iloc[iloc_pos]
            
            # Create task for Technical Analysis (run in executor because it's sync)
            tech_task = loop.run_in_executor(None, self.tech_analyzer.get_full_past_analysis, 
                                             historical_slice_df, current_date_ohlcv)
            tasks_to_gather.append(tech_task)

            # Create task for News Analysis (it's async itself)
            backtest_date = current_date_ohlcv.name.to_pydatetime()
            news_texts = self.data_preparer.get_history_news_for_ticker(ticker, backtest_date)
            news_task = self.news_analyzer.generate_report(ticker, news_texts)
            tasks_to_gather.append(news_task)
            
        # 4. Run all Technical and News tasks in parallel
        logger.info(f"  Running {len(tasks_to_gather)} Technical/News tasks in parallel for '{ticker}'...")
        other_reports = await asyncio.gather(*tasks_to_gather, return_exceptions=True)

        # 5. Assemble and save each report
        logger.info(f"  Assembling and saving {len(selected_datas)} reports for '{ticker}'...")
        for i, iloc_pos in enumerate(valid_target_ilocs):
            backtest_date: datetime = enriched_daily_df.iloc[iloc_pos].name.to_pydatetime()
            
            tech_report_result = other_reports[i * 2]
            news_report_result = other_reports[i * 2 + 1]
            forecasting_report = forecasting_reports[i]

            # Check errors from gather
            if isinstance(tech_report_result, Exception):
                logger.err(f"    - Technical analysis failed for {ticker} at {backtest_date.date()}: {tech_report_result}")
                continue
            if isinstance(news_report_result, Exception):
                logger.err(f"    - News analysis failed for {ticker} at {backtest_date.date()}: {news_report_result}")
                continue
            
            # Assemble final report
            final_report = QuickCheckAnalysisReport(
                ticker=ticker.upper(),
                generated_at_utc=datetime.now(tz=timezone.utc).isoformat(),
                generated_timestamp=int(backtest_date.timestamp()),
                technical_report=tech_report_result,
                forecasting_report=forecasting_report,
                news_report=news_report_result
            )
            
            # Clean and save to database
            cleaned_report_dict = clean_json_outliers(final_report.model_dump())
            report_to_save = QuickCheckAnalysisReport.model_validate(cleaned_report_dict)
            self.backtest_generator.save_report(report_to_save, backtest_date)

        logger.info(f"  -> SUCCESS: Finished processing reports for '{ticker}'.")

    async def generate_backtest_data(self, ticker: str, backtest_dates: list[datetime]) -> None:
        """Main function: Coordinate the entire process of creating and storing backtest data.
        
        Args:
            ticker (str): Stock ticker symbol to generate backtest data for
            backtest_dates (list[datetime]): List of dates to backtest
        """
        start = time.time()
        logger.info("====== STARTING BACKTEST DATA GENERATION PROCESS ======")
        self.check_service_health()
    
        try:
            sector = self.data_preparer.get_sector_code_of(ticker)
            await self._process_single_ticker_for_backtest(ticker, sector, backtest_dates)
        except (ValueError, NoDataError):
            logger.warn(f"[Backtest] Could not find sector for ticker '{ticker}'. Skipping.")
        except Exception as e:
            logger.err(f"  -> UNHANDLED EXCEPTION for ticker '{ticker}': {e}")
        
        end = time.time()
        logger.info(f"====== BACKTEST DATA GENERATION PROCESS COMPLETE IN {(end-start)/60} minutes  ======")
        
if __name__ == '__main__':
    import sys
    sector = sys.argv[1]
    orchestrator = AnalysisOrchestrator()
    orchestrator.export_local_data_for_sector(sector)