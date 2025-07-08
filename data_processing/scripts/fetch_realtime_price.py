import time
from datetime import datetime, timezone
from typing import Literal
import pytz
import yfinance as yf
import schedule
from functools import partial

from utils import TO_FETCH_TICKERS_BY_REGION, REGION_TIME_ZONE, MARKET_OPEN_TIME, MARKET_CLOSE_TIME, FetchException
from db_manager import RedisManager

def is_market_open(region_timezone: str) -> bool:
    try:
        tz = pytz.timezone(region_timezone)
        local_dt = datetime.now(tz)
        local_time = local_dt.time()
        
        is_weekday = local_dt.isoweekday() <= 5
        
        return is_weekday and MARKET_OPEN_TIME <= local_time and MARKET_CLOSE_TIME >= local_time
    except Exception as e:
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
        'last_price': info.last_price,
        'last_volume': info.last_volume,
        'last_update_utc': datetime.now(timezone.utc).isoformat()
    }
    
    redis_mng.add_intraday_candle(ticker=ticker_sym, candle_data=provisional_candle)
    
    print(f"  - Successfully update {ticker_sym} with last price is {info.last_price}")
    
def full_pipeline(region: Literal['americas', 'europe', 'asia_pacific'],
                  redis_mng: RedisManager,
                  relax_time: int = 5):
    region_tz = REGION_TIME_ZONE.get(region)
    
    print(f"--- START REAL-TIME PIPELINE FOR REGION: {region.upper()}, at {datetime.now(timezone.utc).isoformat()} ---")
    
    tickers = TO_FETCH_TICKERS_BY_REGION.get(region)
    
    if is_market_open(region_tz):
        for ticker in tickers:
            try:
                process_single_ticker(ticker, redis_mng)
            except FetchException as e:
                print(f'Error in ticker {ticker}: {e}')
            except Exception as e:
                print(f'Unknown Error in {ticker}: {e}')
            time.sleep(relax_time)
            
        print('Complete cycle')
    else:
        print(f"[{datetime.now(pytz.timezone(region_tz)).strftime('%Y-%m-%d %H:%M:%S')}] Market not open in {region}")
        
def main_orchestrator():
    print("--- REAL-TIME ORCHESTRATOR (SCHEDULE-BASED) HAS BEEN STARTED ---")
    
    redis_mng = RedisManager() # Tạo đối tượng manager một lần
    
    # --- Lập lịch cho các công việc ---
    for region in REGION_TIME_ZONE.keys():
        print(f"Scheduling for region {region.upper()}, run each 15 minute...")
        partial_job = partial(full_pipeline, region=region, redis_mng=redis_mng, relax_time=4)
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