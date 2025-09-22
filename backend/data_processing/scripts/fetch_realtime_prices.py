"""Real-time stock price fetching and processing pipeline.

This module implements a pipeline to fetch real-time stock prices
from Yahoo Finance at scheduled intervals and store them in Redis.
"""

import time
from datetime import datetime, timezone
from functools import partial

import pytz
import schedule
import yfinance as yf
from itapia_common.dblib.services import DataMetadataService, DataPricesService
from itapia_common.dblib.session import (
    get_singleton_rdbms_engine,
    get_singleton_redis_client,
)
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger("Realtime Price Processor")


def _is_market_open_for_ticker(ticker_info: dict) -> bool:
    """Check if the market is open for a specific ticker based on its metadata.

    Args:
        ticker_info (dict): Dictionary containing ticker metadata including
            timezone, open_time, and close_time.

    Returns:
        bool: True if the market is open for the ticker, False otherwise.
    """
    try:
        # Get information from cache
        tz_str = ticker_info["timezone"]
        # open_time_str = ticker_info['open_time'] # Example: "09:30:00"
        # close_time_str = ticker_info['close_time'] # Example: "16:00:00"

        open_time = ticker_info["open_time"]
        close_time = ticker_info["close_time"]

        # Get current time in the exchange's timezone
        tz = pytz.timezone(tz_str)
        local_dt = datetime.now(tz)
        local_time = local_dt.time()

        # Check if it's a weekday
        is_weekday = local_dt.isoweekday() <= 5

        return is_weekday and open_time <= local_time < close_time

    except Exception as e:
        logger.err(f"Error checking market open status: {e}")
        return False


def _process_single_ticker(ticker_sym: str, prices_service: DataPricesService):
    """Process a single ticker to fetch and store its real-time price data.

    Args:
        ticker_sym (str): Ticker symbol to process.
        prices_service (DataPricesService): Service to manage price data storage.
    """
    info = yf.Ticker(ticker_sym).fast_info

    required_keys = ["lastPrice", "dayHigh", "dayLow", "open", "lastVolume"]
    if not all(info.get(k) is not None for k in required_keys):
        logger.warn(f"  - Data not enough: {ticker_sym}. Continue!")
        return

    provisional_candle = {
        "open": info.open,
        "high": info.day_high,
        "low": info.day_low,
        "close": info.last_price,
        "volume": info.last_volume,
        "last_update_utc": datetime.now(timezone.utc).isoformat(),
    }

    prices_service.add_intraday_prices(
        ticker=ticker_sym, candle_data=provisional_candle
    )

    logger.info(
        f"  - Successfully update {ticker_sym} with last price is {info.last_price}"
    )


def full_pipeline(
    metadata_service: DataMetadataService,
    prices_service: DataPricesService,
    relax_time: int = 2,
):
    """Main pipeline that runs periodically to fetch real-time price data.

    It iterates through all active tickers, checks if the market for that
    ticker is open. If so, it calls yfinance to get the latest price
    and writes it to Redis Stream.

    Args:
        metadata_service (DataMetadataService): Service to access ticker metadata.
        prices_service (DataPricesService): Service to manage price data storage.
        relax_time (int, optional): Time to wait (in seconds) between requests. Defaults to 2.
    """
    logger.info(f"--- RUNNING REAL-TIME PIPELINE at {datetime.now().isoformat()} ---")

    # 1. Get information for all active tickers from cache
    # This operation is fast because data is already in memory
    logger.info("Getting metadata of all tickers ...")
    active_tickers_info = metadata_service.metadata_cache
    tickers_to_process = []

    # 2. Filter list of tickers that need to be processed right now
    for ticker, info in active_tickers_info.items():
        if _is_market_open_for_ticker(info):
            tickers_to_process.append(ticker)
        else:
            logger.warn(f"Ticker {ticker} not open, skip.")

    if not tickers_to_process:
        logger.err("No markets are currently open. Skipping cycle.")
        return

    logger.info(
        f"Markets open for {len(tickers_to_process)} tickers: {tickers_to_process[:5]}..."
    )

    # 3. Process filtered tickers
    for ticker in tickers_to_process:
        try:
            _process_single_ticker(ticker, prices_service)
        except Exception as e:
            # Catch general exception to prevent pipeline crash
            logger.err(f"Unknown Error processing ticker {ticker}: {e}")

        time.sleep(relax_time)  # Pause between tickers

    logger.info("--- COMPLETED PIPELINE CYCLE ---")


def main_orchestrator():
    """Main entry point that sets up and runs the real-time data collection schedule.

    This function initializes the required services and uses the `schedule`
    library to repeatedly call `full_pipeline` at fixed intervals (e.g., every minute).
    """
    logger.info("--- REAL-TIME ORCHESTRATOR (SCHEDULE-BASED) HAS BEEN STARTED ---")

    logger.info(f"Scheduling for job, run each 15 minute...")

    engine = get_singleton_rdbms_engine()
    redis_client = get_singleton_redis_client()

    metadata_service = DataMetadataService(engine)
    prices_service = DataPricesService(engine, redis_client)

    partial_job = partial(
        full_pipeline,
        metadata_service=metadata_service,
        prices_service=prices_service,
        relax_time=4,
    )
    schedule.every().hour.at(":00").do(partial_job)
    schedule.every().hour.at(":15").do(partial_job)
    schedule.every().hour.at(":30").do(partial_job)
    schedule.every().hour.at(":45").do(partial_job)
    # schedule.every().hour.at(":40").do(partial_job)
    # schedule.every().hour.at(":50").do(partial_job)

    # Execution loop
    while True:
        schedule.run_pending()
        # Sleep 5 seconds to avoid 100% CPU load
        time.sleep(5)


if __name__ == "__main__":
    main_orchestrator()
