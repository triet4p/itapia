import asyncio
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
    """
    Quản lý toàn bộ vòng đời của dữ liệu backtest cho một ticker duy nhất.
    
    Bao gồm việc chọn ngày, yêu cầu tạo báo cáo, chờ đợi hoàn thành,
    và tải dữ liệu cuối cùng vào bộ nhớ.
    """

    def __init__(self, ticker: str, data_preparer: BacktestDataPreparer):
        self.ticker = ticker
        self.data_preparer = data_preparer
        
        self.job_id: Optional[str] = None # ID của tác vụ tạo dữ liệu|

        # Dữ liệu sẽ được tải vào đây
        self.ohlcv_df: Optional[pd.DataFrame] = None
        self.historical_reports: List[QuickCheckAnalysisReport] = []

        # Các biến quản lý trạng thái
        self.status: BACKTEST_CONTEXT_STATUS = 'IDLE'
        self.data_ready_event = asyncio.Event()

    async def prepare_data_async(self):
        """
        Hàm điều phối chính: Kích hoạt toàn bộ quy trình chuẩn bị dữ liệu.
        Đây là điểm vào duy nhất từ bên ngoài.
        """
        if self.status != 'IDLE':
            logger.warn(f"Preparation for ticker {self.ticker} already started. Current status: {self.status}")
            return
            
        logger.info(f"Starting data preparation for ticker: {self.ticker}")
        self.status = 'PREPARING'
        
        try:
            # 1. Lấy dữ liệu OHLCV thô
            self.ohlcv_df = self.data_preparer.get_daily_ohlcv_for_ticker(self.ticker, limit=5000)
            if self.ohlcv_df.empty:
                raise ValueError("Failed to fetch OHLCV data.")

            # 2. Chọn các điểm backtest
            
            selector = BacktestPointSelector(
                self.ohlcv_df,
                selector_start=cfg.SELECTOR_START_DATE,
                selector_end=cfg.SELECTOR_END_DATE,
            )
            
            timestamps_to_request = (selector
                                     .add_monthly_points(day_of_month=cfg.MONTHLY_DAY)
                                     .add_significant_points(max_points=cfg.MAX_SPECIAL_POINTS)
                                     .get_points_as_timestamps())
            
            if not timestamps_to_request:
                logger.warn(f"No backtest points selected for ticker {self.ticker}. Marking as ready.")
                self.status = 'READY'
                self.data_ready_event.set()
                return

            # 3. Gửi yêu cầu tạo báo cáo đến AI Service Quick
            response = await api_caller.trigger_backtest_generation_task(
                ticker=self.ticker,
                timestamps=timestamps_to_request,
            )
            self.job_id = response.job_id
            
            # 4. Bắt đầu vòng lặp hỏi thăm (polling) để chờ hoàn thành
            await self._poll_for_completion()

        except Exception as e:
            logger.err(f"Failed to prepare data for {self.ticker}: {e}")
            self.status = 'FAILED'
            # Vẫn set event để bất kỳ ai đang chờ không bị treo, nhưng họ sẽ thấy status là FAILED
            self.data_ready_event.set()

    async def _poll_for_completion(self):
        """
        Vòng lặp bất đồng bộ để kiểm tra trạng thái của tác vụ tạo dữ liệu.
        """
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
                    await self._load_reports_from_db()
                    self.status = 'READY'
                    self.data_ready_event.set()
                    break # Thoát khỏi vòng lặp
                
                elif response.status == 'FAILED':
                    logger.err("Backtest generation task failed on AI Service Quick.")
                    self.status = 'FAILED'
                    self.data_ready_event.set()
                    break # Thoát khỏi vòng lặp
                    
                # Nếu vẫn đang 'RUNNING' hoặc 'IDLE', đợi và thử lại
                await asyncio.sleep(polling_interval)
                
            except Exception as e:
                logger.err(f"Error during polling for {self.ticker}: {e}")
                self.status = 'FAILED'
                self.data_ready_event.set()
                break

    async def _load_reports_from_db(self):
        """
        Tải tất cả các báo cáo lịch sử từ CSDL sau khi đã được xác nhận là hoàn thành.
        """
        # Đây là một tác vụ có thể liên quan đến I/O CSDL, nên chạy trong executor là tốt nhất
        loop = asyncio.get_running_loop()
        self.historical_reports = await loop.run_in_executor(
            None, # Sử dụng executor mặc định
            self.data_preparer.get_backtest_reports_for_ticker,
            self.ticker
        )
        logger.info(f"Successfully loaded {len(self.historical_reports)} historical reports for {self.ticker}.")
    
    async def wait_for_data(self):
        """
        Cung cấp một cách để các module khác chờ cho đến khi dữ liệu sẵn sàng.
        """
        await self.data_ready_event.wait()
        
    def get_reports(self) -> List[QuickCheckAnalysisReport]:
        """
        Getter an toàn để truy cập dữ liệu sau khi đã sẵn sàng.
        """
        if self.status != 'READY':
            raise BacktestError(f"Data is not ready for ticker {self.ticker}. Current status: {self.status}")
        return self.historical_reports

    def get_ohlcv(self) -> pd.DataFrame:
        """
        Getter an toàn để truy cập dữ liệu OHLCV.
        """
        if self.ohlcv_df is None:
            raise BacktestError(f"OHLCV data has not been loaded for ticker {self.ticker}.")
        return self.ohlcv_df
    

class BacktestContextManager:
    """
    Quản đốc điều phối việc chuẩn bị dữ liệu backtest, chạy song song với
    số lượng giới hạn để không làm quá tải AI Service Quick.
    """
    def __init__(self, data_preparer: BacktestDataPreparer):
        self.data_preparer = data_preparer
        self.contexts: Dict[str, BacktestContext] = {}

    async def _prepare_single_context(self, ticker: str, semaphore: asyncio.Semaphore):
        """
        Hàm worker: Thực hiện toàn bộ quy trình cho một ticker duy nhất,
        được kiểm soát bởi một semaphore.
        """
        async with semaphore: # Chờ để có một "slot" trống
            logger.info(f"Starting preparation for ticker: {ticker}...")
            context = BacktestContext(
                ticker=ticker,
                data_preparer=self.data_preparer
            )
            self.contexts[ticker] = context
            # prepare_data_async giờ đây sẽ là phiên bản gửi yêu cầu cho 1 ticker
            # và poll cho đến khi hoàn thành
            await context.prepare_data_async() 

    async def prepare_all_contexts(self):
        """
        Khởi tạo và chạy quá trình chuẩn bị dữ liệu cho tất cả các ticker song song,
        với mức độ song song được giới hạn.
        """
        # Giới hạn chỉ chạy 5 ticker cùng một lúc để không làm quá tải AI Quick
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
        """
        Lấy context đã được chuẩn bị cho một ticker cụ thể.
        """
        return self.contexts.get(ticker)

    def get_ready_contexts(self) -> List[BacktestContext]:
        """
        Trả về một danh sách tất cả các context đã ở trạng thái 'READY'.
        Đây là danh sách mà FitnessEvaluator sẽ làm việc.
        """
        return [ctx for ctx in self.contexts.values() if ctx.status == 'READY']

    def log_summary(self):
        """Ghi log tóm tắt về trạng thái của tất cả các context."""
        total = len(self.contexts)
        ready_count = len([ctx for ctx in self.contexts.values() if ctx.status == 'READY'])
        failed_count = len([ctx for ctx in self.contexts.values() if ctx.status == 'FAILED'])
        preparing_count = len([ctx for ctx in self.contexts.values() if ctx.status == 'PREPARING'])
        
        logger.info("--- Backtest Context Manager Summary ---")
        logger.info(f"Total Tickers: {total}")
        logger.info(f"  - Ready: {ready_count}")
        logger.info(f"  - Failed: {failed_count}")
        logger.info(f"  - Still Preparing: {preparing_count}")
        logger.info("------------------------------------")