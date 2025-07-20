from datetime import datetime, timezone
import time
import pytz

import schedule
from functools import partial

import yfinance as yf

from itapia_common.dblib.session import get_singleton_rdbms_engine, get_singleton_redis_client
from itapia_common.dblib.crud.general_update import bulk_insert
from itapia_common.dblib.crud.metadata import get_ticker_metadata
from itapia_common.dblib.crud.prices import add_intraday_candle
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Realtime Price Processor')

def _is_market_open_for_ticker(ticker_info: dict) -> bool:
    """
    Kiểm tra xem thị trường có đang mở cửa cho một ticker cụ thể không,
    dựa trên thông tin metadata của nó.
    """
    try:
        # Lấy thông tin từ cache
        tz_str = ticker_info['timezone']
        #open_time_str = ticker_info['open_time'] # Ví dụ: "09:30:00"
        #close_time_str = ticker_info['close_time'] # Ví dụ: "16:00:00"

        open_time = ticker_info['open_time']
        close_time = ticker_info['close_time']
        
        # Lấy thời gian hiện tại theo đúng múi giờ của sàn
        tz = pytz.timezone(tz_str)
        local_dt = datetime.now(tz)
        local_time = local_dt.time()
        
        # Kiểm tra ngày trong tuần
        is_weekday = local_dt.isoweekday() <= 5
        
        return is_weekday and open_time <= local_time < close_time

    except Exception as e:
        logger.err(f"Error checking market open status: {e}")
        return False
    
def _process_single_ticker(ticker_sym: str):

    info = yf.Ticker(ticker_sym).fast_info
    
    required_keys = ['lastPrice', 'dayHigh', 'dayLow', 'open', 'lastVolume']
    if not all(info.get(k) is not None for k in required_keys):
        logger.warn(f"  - Data not enough: {ticker_sym}. Continue!")
        return
    
    provisional_candle = {
        'open': info.open,
        'high': info.day_high,
        'low': info.day_low,
        'close': info.last_price,
        'volume': info.last_volume,
        'last_update_utc': datetime.now(timezone.utc).isoformat()
    }
    
    redis_client = get_singleton_redis_client()
    
    add_intraday_candle(redis_client=redis_client, ticker=ticker_sym, candle_data=provisional_candle)
    
    logger.info(f"  - Successfully update {ticker_sym} with last price is {info.last_price}")
    
def full_pipeline(relax_time: int = 2):
    """Pipeline chính, chạy định kỳ để lấy dữ liệu giá real-time.

    Nó lặp qua tất cả các ticker đang hoạt động, kiểm tra xem thị trường của
    ticker đó có đang mở cửa không. Nếu có, nó sẽ gọi yfinance để lấy giá
    mới nhất và ghi vào Redis Stream.

    Args:
        db_mng (PostgreDBManager): Instance của DB manager.
        redis_mng (RedisManager): Instance của Redis manager.
        relax_time (int, optional): Thời gian nghỉ (giây) giữa các request. Mặc định là 2.
    """
    logger.info(f"--- RUNNING REAL-TIME PIPELINE at {datetime.now().isoformat()} ---")
    
    # 1. Lấy thông tin của tất cả các ticker đang hoạt động từ cache
    # Thao tác này rất nhanh vì dữ liệu đã có trong bộ nhớ
    logger.info("Getting metadata of all tickers ...")
    engine = get_singleton_rdbms_engine()
    active_tickers_info = get_ticker_metadata(rdbms_engine=engine)
    tickers_to_process = []
    
    # 2. Lọc ra danh sách các ticker cần xử lý ngay bây giờ
    for ticker, info in active_tickers_info.items():
        if _is_market_open_for_ticker(info):
            tickers_to_process.append(ticker)
        else:
            logger.warn(f'Ticker {ticker} not open, skip.')
    
    if not tickers_to_process:
        logger.err("No markets are currently open. Skipping cycle.")
        return
        
    logger.info(f"Markets open for {len(tickers_to_process)} tickers: {tickers_to_process[:5]}...")
    
    # 3. Xử lý các ticker đã lọc
    for ticker in tickers_to_process:
        try:
            _process_single_ticker(ticker)
        except Exception as e:
            # Bắt lỗi chung để pipeline không bị sập
            logger.err(f'Unknown Error processing ticker {ticker}: {e}')
        
        time.sleep(relax_time) # Nghỉ một chút giữa các ticker

    logger.info('--- COMPLETED PIPELINE CYCLE ---')
        
def main_orchestrator():
    """Điểm vào chính, thiết lập và chạy lịch trình thu thập dữ liệu real-time.

    Hàm này khởi tạo các manager cần thiết và sử dụng thư viện `schedule`
    để lặp lại việc gọi `full_pipeline` theo một chu kỳ cố định (ví dụ: mỗi phút).
    """
    logger.info("--- REAL-TIME ORCHESTRATOR (SCHEDULE-BASED) HAS BEEN STARTED ---")
    
    logger.info(f"Scheduling for job, run each 15 minute...")
    partial_job = partial(full_pipeline, relax_time=4)
    schedule.every().hour.at(":00").do(partial_job)
    schedule.every().hour.at(":15").do(partial_job)
    schedule.every().hour.at(":30").do(partial_job)
    schedule.every().hour.at(":45").do(partial_job)
    # schedule.every().hour.at(":40").do(partial_job)
    # schedule.every().hour.at(":50").do(partial_job)
        
    # Vòng lặp thực thi
    while True:
        schedule.run_pending()
        # Nghỉ 5 giây để tránh CPU load 100%
        time.sleep(5)
        
if __name__ == '__main__':
    main_orchestrator()