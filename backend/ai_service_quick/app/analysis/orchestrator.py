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
    """
    Quét đệ quy qua một đối tượng (dict, list) và thay thế các giá trị
    numpy/float đặc biệt (inf, -inf, nan) bằng None.
    """
    if isinstance(obj, dict):
        return {k: clean_json_outliers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_outliers(elem) for elem in obj]
    elif isinstance(obj, (np.integer, np.floating, float)):
        # Kiểm tra xem có phải là nan, inf, hoặc -inf không
        if not np.isfinite(obj):
            return None  # Thay thế bằng None (sẽ trở thành null trong JSON)
    return obj


class AnalysisOrchestrator:
    """
    Super Orchestrator ("CEO") cho toàn bộ quy trình Quick Check (phiên bản Async).
    Nó điều phối các orchestrator của từng module lớn để thực hiện các
    quy trình nghiệp vụ hoàn chỉnh.
    """
    def __init__(self, data_preparer: DataPrepareOrchestrator,
                 tech_analyzer: TechnicalOrchestrator,
                 forecaster: ForecastingOrchestrator,
                 news_analyzer: NewsOrchestrator,
                 explainer: AnalysisExplainerOrchestrator,
                 backtest_orchestrator: BacktestOrchestrator):
        # Khởi tạo các "Trưởng phòng"
        self.data_preparer = data_preparer
        self.tech_analyzer = tech_analyzer
        self.forecaster = forecaster
        self.news_analyzer = news_analyzer
        self.explainer = explainer
        self.backtest_generator = backtest_orchestrator
        self.is_active = False
        
    def get_all_tickers(self):
        return self.data_preparer.get_all_tickers()

    # === HÀM TIỆN ÍCH CHO TỪNG MODULE (ASYNC HELPERS) ===

    def _prepare_and_run_technical_analysis(self, daily_df: pd.DataFrame, intraday_df: pd.DataFrame, 
                                            daily_analysis_type: str, required_type: str) -> TechnicalReport:
        """
        Giai đoạn Phân tích Kỹ thuật (đồng bộ vì các tác vụ rất nhanh).
        """
        logger.info("CEO -> TechAnalyzer: Performing technical analysis...")
        # Đây là tác vụ nhanh, có thể chạy đồng bộ.
        return self.tech_analyzer.get_full_analysis(
            daily_df, 
            intraday_df,
            required_type=required_type,
            daily_analysis_type=daily_analysis_type
        )

    async def _prepare_and_run_forecasting(self, ticker: str, daily_df: pd.DataFrame) -> ForecastingReport:
        """
        Giai đoạn Dự báo (bất đồng bộ).
        """
        logger.info("CEO -> Forecaster: Preparing data and running forecast...")
        # 1. Chuẩn bị dữ liệu đầu vào (nhanh, đồng bộ)
        sector = self.data_preparer.get_sector_code_of(ticker)
        features_df = self.tech_analyzer.get_daily_features(daily_df)
        latest_features = features_df.iloc[-1:]

        # 2. Gọi hàm generate_report (nặng, bất đồng bộ)
        return await self.forecaster.generate_report(latest_features, ticker, sector)

    async def _prepare_and_run_news_analysis(self, ticker: str) -> NewsAnalysisReport:
        """
        Giai đoạn Phân tích Tin tức (bất đồng bộ).
        """
        logger.info("CEO -> NewsAnalyzer: Preparing data and running news analysis...")
        # 1. Chuẩn bị dữ liệu đầu vào (nhanh, đồng bộ)
        news_texts = self.data_preparer.get_all_news_text_for_ticker(ticker)

        # 2. Gọi hàm generate_report (nặng, bất đồng bộ)
        return await self.news_analyzer.generate_report(ticker, news_texts)
    
    def check_service_health(self):
        if not self.is_active:
            raise NotReadyServiceError('Service is not ready! Check after 5-10 minutes')
        
    def check_data_avaiable(self, ticker: str):
        if not self.data_preparer.is_exist(ticker):
            raise NoDataError(f'Not found ticker {ticker}')

    # === HÀM CHÍNH ĐIỀU PHỐI (QUY TRÌNH 1) ===
    
    async def get_technical_report(self, ticker: str,
                                   daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                                   required_type: Literal['daily', 'intraday', 'all']='all'
                                   ) -> TechnicalReport:
        self.check_service_health()
        self.check_data_avaiable(ticker)
        
        logger.info(f"--- CEO (ASYNC): Initiating TECHNICAL-ONLY analysis for '{ticker}' ---")
        
        # --- BƯỚC 1: LẤY DỮ LIỆU THÔ (ĐỒNG BỘ) ---
        logger.info("CEO -> DataPreparer: Fetching price data...")
        daily_df = self.data_preparer.get_daily_ohlcv_for_ticker(ticker)
        intraday_df = self.data_preparer.get_intraday_ohlcv_for_ticker(ticker)

        if daily_df.empty: # Chỉ cần kiểm tra daily_df vì forecasting và technical chính dựa vào nó
            logger.err(f"No daily data available for ticker {ticker}.")
            raise NoDataError(f"No daily data available for ticker {ticker}.")
        
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(
            None, self._prepare_and_run_technical_analysis, 
            daily_df, intraday_df, daily_analysis_type, required_type
        )
        return report
    
    async def get_forecasting_report(self, ticker: str) -> ForecastingReport:
        self.check_service_health()
        self.check_data_avaiable(ticker)
        
        logger.info(f"--- CEO (ASYNC): Initiating FORECASTING-ONLY analysis for '{ticker}' ---")
        
        # --- BƯỚC 1: LẤY DỮ LIỆU THÔ (ĐỒNG BỘ) ---
        logger.info("CEO -> DataPreparer: Fetching price data...")
        daily_df = self.data_preparer.get_daily_ohlcv_for_ticker(ticker)

        if daily_df.empty: # Chỉ cần kiểm tra daily_df vì forecasting và technical chính dựa vào nó
            logger.err(f"No daily data available for ticker {ticker}.")
            raise NoDataError(f"No daily data available for ticker {ticker}.")
        
        return await self._prepare_and_run_forecasting(ticker, daily_df)
    
    async def get_news_report(self, ticker: str) -> NewsAnalysisReport:
        self.check_service_health()
        self.check_data_avaiable(ticker)
        
        logger.info(f"--- CEO: Initiating NEWS-ONLY analysis for '{ticker}' ---")
        
        return await self._prepare_and_run_news_analysis(ticker)

    async def get_full_analysis_report(self, ticker: str, 
                                       daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                                       required_type: Literal['daily', 'intraday', 'all']='all'
                                      ) -> QuickCheckAnalysisReport:
        """
        Tạo báo cáo phân tích A-Z cho một ticker, chạy các module nặng song song.
        """
        self.check_service_health()
        self.check_data_avaiable(ticker)
        
        logger.info(f"--- CEO (ASYNC): Initiating full analysis for ticker '{ticker}' ---")
        
        # --- BƯỚC 1: LẤY DỮ LIỆU THÔ (ĐỒNG BỘ) ---
        logger.info("CEO -> DataPreparer: Fetching price data...")
        daily_df = self.data_preparer.get_daily_ohlcv_for_ticker(ticker)
        intraday_df = self.data_preparer.get_intraday_ohlcv_for_ticker(ticker)

        if daily_df.empty: # Chỉ cần kiểm tra daily_df vì forecasting và technical chính dựa vào nó
            logger.err(f"No daily data available for ticker {ticker}.")
            raise NoDataError(f"No daily data available for ticker {ticker}.")

        # --- BƯỚC 2: CHẠY TẤT CẢ CÁC MODULE SONG SONG ---
        logger.info("CEO: Dispatching all analysis modules to run in parallel...")
        
        # Chạy Phân tích Kỹ thuật (tác vụ nhanh) trong executor để không block
        # Mặc dù nhanh, đưa vào executor là cách làm an toàn nhất để đảm bảo non-blocking.
        loop = asyncio.get_running_loop()
        technical_task = loop.run_in_executor(
            None, self._prepare_and_run_technical_analysis, 
            daily_df, intraday_df, daily_analysis_type, required_type
        )

        # Tạo các task cho các module nặng
        forecasting_task = self._prepare_and_run_forecasting(ticker, daily_df)
        news_task = self._prepare_and_run_news_analysis(ticker)

        # Sử dụng gather để chờ tất cả hoàn thành
        results = await asyncio.gather(
            technical_task, 
            forecasting_task, 
            news_task,
            return_exceptions=True # Rất quan trọng để xử lý lỗi
        )

        # --- BƯỚC 3: KIỂM TRA LỖI VÀ TỔNG HỢP KẾT QUẢ ---
        
        # Giải nén kết quả
        technical_report, forecasting_report, news_report = results

        # Kiểm tra xem có module nào bị lỗi không
        if isinstance(technical_report, Exception):
            logger.err(f"Technical analysis failed for {ticker}: {technical_report}")
            raise MissingReportError(f"Technical analysis module failed.")
        if isinstance(forecasting_report, Exception):
            logger.err(f"Forecasting failed for {ticker}: {forecasting_report}")
            raise MissingReportError(f"Forecasting module failed.")
        if isinstance(news_report, Exception):
            logger.err(f"News analysis failed for {ticker}: {news_report}")
            raise MissingReportError(f"News analysis module failed.")

        # --- BƯỚC 4: TẠO BÁO CÁO CUỐI CÙNG ---
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
        
        # Dọn dẹp các giá trị NaN/inf trước khi trả về
        cleaned_report_dict = clean_json_outliers(final_report.model_dump())
        return QuickCheckAnalysisReport.model_validate(cleaned_report_dict)
    
    async def get_full_explaination_report(
        self, 
        ticker: str, 
        daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
        required_type: Literal['daily', 'intraday', 'all']='all',
        explain_type: ExplainReportType = 'all'
    ) -> str:
        """
        Tái sử dụng báo cáo JSON đầy đủ và tạo ra một bản tóm tắt plain-text.
        """
        logger.info(f"--- CEO: Initiating PLAIN-TEXT explanation for '{ticker}' ---")
        
        # BƯỚC 1: Gọi hàm chính để lấy dữ liệu có cấu trúc
        json_report = await self.get_full_analysis_report(
            ticker, daily_analysis_type, required_type
        )

        # BƯỚC 2: Gọi đến Explainer Orchestrator để "dịch" báo cáo
        explanation_text = self.explainer.explain(
            report=json_report, 
            report_type=explain_type
        )
        
        return explanation_text
    
    async def preload_all_caches(self):
        """
        Kích hoạt song song quy trình làm nóng cache cho TẤT CẢ các sub-module.
        """
        logger.info("--- CEO: Starting PARALLEL pre-warming for all sub-modules ---")
        
        # Chuẩn bị các tham số cần thiết
        sectors = self.data_preparer.get_all_sectors_code()
        #sectors = ['TECH']
        # 1. Tạo một danh sách các "công việc lớn" cần thực hiện
        # Mỗi công việc là một lần gọi đến hàm preload của một "trưởng phòng"
        tasks = [
            self.forecaster.preload_caches_for_all_sectors(sectors),
            self.news_analyzer.preload_caches()
            # Trong tương lai có thể thêm các module khác ở đây
            # self.another_module.preload()
        ]

        # 2. Sử dụng asyncio.gather để chạy tất cả các công việc song song và CHỜ chúng
        # SỬA LỖI QUAN TRỌNG: Thêm `await` ở phía trước
        # Dùng return_exceptions=True để một module lỗi không làm sập toàn bộ quá trình
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # (Tùy chọn nhưng khuyến khích) Kiểm tra kết quả để ghi log nếu có lỗi
        module_names = ["News Analysis"]
        has_errors = False
        for result, name in zip(results, module_names):
            if isinstance(result, Exception):
                logger.err(f"  - Pre-warming FAILED for module '{name}': {result}")
                has_errors = True
            else:
                logger.info(f"  - Pre-warming complete for module '{name}'.")

        # 3. Chỉ sau khi TẤT CẢ đã hoàn thành, mới đặt trạng thái là active
        if not has_errors:
            self.is_active = True
            logger.info("--- CEO: All modules pre-warmed successfully. Service is now active. ---")
        else:
            logger.warn("--- CEO: Pre-warming process completed with errors. Service might not be fully functional. ---")
            
    def prepare_training_data_for_sector(self, sector_code: str) -> pd.DataFrame:
        """
        QUY TRÌNH 2: Chuẩn bị một DataFrame lớn, sẵn sàng để huấn luyện,
        cho tất cả các ticker trong một nhóm ngành.
        """
        logger.info(f"--- CEO: Preparing training data for sector '{sector_code}' ---")
        
        # BƯỚC 1: LẤY DỮ LIỆU GỘP CỦA CẢ NGÀNH
        logger.info("CEO -> DataPreparer: Fetching and transforming sector data...")
        sector_ohlcv_df = self.data_preparer.get_daily_ohlcv_for_sector(sector_code)
        
        if sector_ohlcv_df.empty:
            logger.err(f"No data found for sector {sector_code}.")
            return pd.DataFrame()

        # BƯỚC 2: TẠO FEATURES CHO DỮ LIỆU ĐÃ GỘP
        # Lưu ý: Cần lặp qua từng ticker để tạo feature cho đúng
        logger.info("CEO -> TechAnalyzer: Generating features for sector data...")
        all_enriched_dfs = []
        for ticker, group_df in sector_ohlcv_df.groupby('ticker'):
            logger.info(f"  - Generating features for {ticker}...")
            enriched_ticker_df = self.tech_analyzer.get_daily_features(group_df)
            all_enriched_dfs.append(enriched_ticker_df)
        
        enriched_sector_df = pd.concat(all_enriched_dfs)

        # BƯỚC 3 (TƯƠNG LAI): TẠO TARGETS
        # training_ready_df = self.forecasting_pipeline.create_targets(enriched_sector_df)
        
        logger.info(f"--- CEO: Training data for '{sector_code}' is ready. ---")
        return enriched_sector_df # Tạm thời trả về df đã có features
    
    def export_local_data_for_sector(self, sector_code: str):
        df = self.prepare_training_data_for_sector(sector_code)
        df.to_csv(f'/ai-service-quick/local/training_{sector_code}.csv')
        
    # =================================================================
    # SECTION: BACKTESTING DATA GENERATION - ĐÃ TÁI CẤU TRÚC
    # =================================================================

    async def _process_single_ticker_for_backtest(self, ticker: str, sector: str):
        """
        Hàm hỗ trợ: Thực hiện toàn bộ quy trình tạo dữ liệu backtest cho MỘT ticker duy nhất.
        """
        logger.info(f"  -> Processing Ticker: '{ticker}'")
        loop = asyncio.get_running_loop()

        # 1. Lấy dữ liệu lịch sử và các điểm cần backtest
        full_daily_df = self.data_preparer.get_daily_ohlcv_for_ticker(ticker, limit=5000)
        if full_daily_df.empty:
            logger.warn(f"  No daily data for '{ticker}'. Skipping ticker.")
            return
        
        featured_df = self.tech_analyzer.get_daily_features(full_daily_df).copy()

        selected_datas = self.backtest_generator.select_backtest_datas(featured_df)
        if selected_datas.empty:
            logger.warn(f"  No valid historical data points for '{ticker}'. Skipping ticker.")
            return

        # 2. Chạy module nặng nhất (Forecasting) một lần cho tất cả các điểm dữ liệu
        forecasting_reports = await self.forecaster.get_history_reports(
            latest_enriched_datas=selected_datas, ticker=ticker, sector=sector
        )
        if len(forecasting_reports) != len(selected_datas):
            logger.err(f"  Mismatch between selected data points ({len(selected_datas)}) and forecasts ({len(forecasting_reports)}). Skipping ticker.")
            return

        # 3. Chuẩn bị các tác vụ Technical và News để chạy song song
        tasks_to_gather = []
        # Tạo DatetimeIndex một lần và lặp qua nó
        backtest_timestamps = pd.to_datetime(selected_datas.index)
        for backtest_date_idx in backtest_timestamps:
            backtest_date = backtest_date_idx.to_pydatetime()
            
            # Chuẩn bị dữ liệu slice cho technical
            historical_slice_df = full_daily_df[full_daily_df.index <= backtest_date_idx]
            
            # Tạo task cho Technical Analysis (chạy trong executor vì là sync)
            tech_task = loop.run_in_executor(None, self._prepare_and_run_technical_analysis, 
                                             historical_slice_df, pd.DataFrame(), 'medium', 'daily')
            tasks_to_gather.append(tech_task)

            # Tạo task cho News Analysis (bản thân nó là async)
            news_texts = self.data_preparer.get_history_news_for_ticker(ticker, backtest_date)
            news_task = self.news_analyzer.generate_report(ticker, news_texts)
            tasks_to_gather.append(news_task)
            
        # 4. Chạy song song tất cả các tác vụ Technical và News
        logger.info(f"  Running {len(tasks_to_gather)} Technical/News tasks in parallel for '{ticker}'...")
        other_reports = await asyncio.gather(*tasks_to_gather, return_exceptions=True)

        # 5. Lắp ráp và lưu từng báo cáo
        logger.info(f"  Assembling and saving {len(selected_datas)} reports for '{ticker}'...")
        for i, backtest_date_idx in enumerate(backtest_timestamps):
            backtest_date = backtest_date_idx.to_pydatetime()
            
            tech_report_result = other_reports[i * 2]
            news_report_result = other_reports[i * 2 + 1]
            forecasting_report = forecasting_reports[i]

            # Kiểm tra lỗi từ gather
            if isinstance(tech_report_result, Exception):
                logger.err(f"    - Technical analysis failed for {ticker} at {backtest_date.date()}: {tech_report_result}")
                continue
            if isinstance(news_report_result, Exception):
                logger.err(f"    - News analysis failed for {ticker} at {backtest_date.date()}: {news_report_result}")
                continue
            
            # Lắp ráp báo cáo cuối cùng
            final_report = QuickCheckAnalysisReport(
                ticker=ticker.upper(),
                generated_at_utc=datetime.now(tz=timezone.utc).isoformat(),
                generated_timestamp=int(backtest_date.timestamp()),
                technical_report=tech_report_result,
                forecasting_report=forecasting_report,
                news_report=news_report_result
            )
            
            # Dọn dẹp và lưu vào CSDL
            cleaned_report_dict = clean_json_outliers(final_report.model_dump())
            report_to_save = QuickCheckAnalysisReport.model_validate(cleaned_report_dict)
            self.backtest_generator.save_report(report_to_save, backtest_date)

        logger.info(f"  -> SUCCESS: Finished processing reports for '{ticker}'.")

    async def generate_backtest_data(self, tickers: list[str]):
        """
        Hàm chính: Điều phối toàn bộ quy trình tạo và lưu trữ dữ liệu backtest.
        """
        start = time.time()
        logger.info("====== STARTING BACKTEST DATA GENERATION PROCESS ======")
        self.check_service_health()
        
        self.backtest_generator.add_backtest_dates_from_cfg()
        
        tickers_by_sector = {}
        for ticker in tickers:
            try:
                sector = self.data_preparer.get_sector_code_of(ticker)
                if sector not in tickers_by_sector: 
                    tickers_by_sector[sector] = []
                tickers_by_sector[sector].append(ticker)
            except (ValueError, NoDataError):
                logger.warn(f"[Backtest] Could not find sector for ticker '{ticker}'. Skipping.")
                continue

        for sector, sector_tickers in tickers_by_sector.items():
            logger.info(f"--- Processing Sector: '{sector}' ({len(sector_tickers)} tickers) ---")
            for ticker in sector_tickers:
                try:
                    await self._process_single_ticker_for_backtest(ticker, sector)
                except Exception as e:
                    logger.err(f"  -> UNHANDLED EXCEPTION for ticker '{ticker}': {e}")
                    continue
        
        end = time.time()
        logger.info(f"====== BACKTEST DATA GENERATION PROCESS COMPLETE IN {(end-start)/60} minutes  ======")
        
if __name__ == '__main__':
    import sys
    sector = sys.argv[1]
    orchestrator = AnalysisOrchestrator()
    orchestrator.export_local_data_for_sector(sector)