from datetime import datetime, timezone, time as dt_time
import time
from typing import Literal
import pytz
import yfinance as yf
import schedule
from functools import partial

from db_manager import PostgreDBManager, RedisManager

def is_market_open_for_ticker(ticker_info: dict) -> bool:
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
        print(f"Error checking market open status: {e}")
        return False
    
def process_single_ticker(ticker_sym: str, redis_mng: RedisManager):

    info = yf.Ticker(ticker_sym).fast_info
    
    required_keys = ['lastPrice', 'dayHigh', 'dayLow', 'open', 'lastVolume']
    if not all(info.get(k) is not None for k in required_keys):
        print(f"  - Data not enough: {ticker_sym}. Continue!")
        return
    
    provisional_candle = {
        'open': info.open,
        'high': info.day_high,
        'low': info.day_low,
        'close': info.last_price,
        'volume': info.last_volume,
        'last_update_utc': datetime.now(timezone.utc).isoformat()
    }
    
    redis_mng.add_intraday_candle(ticker=ticker_sym, candle_data=provisional_candle)
    
    print(f"  - Successfully update {ticker_sym} with last price is {info.last_price}")
    
def full_pipeline(db_mng: PostgreDBManager, redis_mng: RedisManager, relax_time: int = 2):
    """
    Pipeline chính, chạy định kỳ (ví dụ: mỗi phút).
    Nó sẽ lặp qua tất cả các ticker và chỉ xử lý những ticker có thị trường đang mở.
    """
    print(f"--- RUNNING REAL-TIME PIPELINE at {datetime.now().isoformat()} ---")
    
    # 1. Lấy thông tin của tất cả các ticker đang hoạt động từ cache
    # Thao tác này rất nhanh vì dữ liệu đã có trong bộ nhớ
    active_tickers_info = db_mng.get_active_tickers_with_info()
    tickers_to_process = []
    
    # 2. Lọc ra danh sách các ticker cần xử lý ngay bây giờ
    for ticker, info in active_tickers_info.items():
        if is_market_open_for_ticker(info):
            tickers_to_process.append(ticker)
        else:
            print(f'Ticker {ticker} not open, skip.')
    
    if not tickers_to_process:
        print("No markets are currently open. Skipping cycle.")
        return
        
    print(f"Markets open for {len(tickers_to_process)} tickers: {tickers_to_process[:5]}...")
    
    # 3. Xử lý các ticker đã lọc
    for ticker in tickers_to_process:
        try:
            process_single_ticker(ticker, redis_mng)
        except Exception as e:
            # Bắt lỗi chung để pipeline không bị sập
            print(f'Unknown Error processing ticker {ticker}: {e}')
        
        time.sleep(relax_time) # Nghỉ một chút giữa các ticker

    print('--- COMPLETED PIPELINE CYCLE ---')
        
def main_orchestrator():
    print("--- REAL-TIME ORCHESTRATOR (SCHEDULE-BASED) HAS BEEN STARTED ---")
    
    redis_mng = RedisManager() # Tạo đối tượng manager một lần
    db_mng = PostgreDBManager()
    
    print(f"Scheduling for job, run each 15 minute...")
    partial_job = partial(full_pipeline, db_mng=db_mng, redis_mng=redis_mng, relax_time=4)
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