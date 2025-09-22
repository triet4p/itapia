"""Data preparation utilities for backtesting."""

from datetime import datetime
from typing import Any, Dict

import pandas as pd
from itapia_common.dblib.services import (
    APIMetadataService,
    APIPricesService,
    BacktestReportService,
)
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger("Backtest Data Preparer")


def transform_single_ticker_response(json_res: Dict[str, Any]) -> pd.DataFrame:
    """Convert JSON response for a single ticker into a DataFrame.

    DataFrame will have a DatetimeIndex.

    Args:
        json_res (Dict[str, Any]): JSON response containing 'metadata' and 'datas'.

    Returns:
        pd.DataFrame: OHLCV DataFrame with DatetimeIndex.

    Raises:
        ValueError: If response is missing required keys.
    """
    # --- STEP 1: VALIDATE AND EXTRACT DATA ---
    logger.info("Transforming single ticker response ...")
    metadata = json_res.get("metadata")
    if not metadata:
        raise ValueError("Response is missing 'metadata' key.")

    data_points = json_res.get("datas")
    if not data_points:
        logger.warn(
            f"Empty data points for ticker {metadata.get('ticker')}. Returning empty DataFrame."
        )
        return pd.DataFrame()

    # --- STEP 2: CONVERT LIST OF DICTS TO DATAFRAME ---
    df = pd.DataFrame(data_points)

    # Check for required columns in data_points
    required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(
            f"Data points are missing required keys. Expected: {required_cols}"
        )

    # --- STEP 3: PROCESS TIME INDEX ---
    # Convert timestamp column (Unix epoch) to DatetimeIndex UTC
    df["datetime_utc"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    df.set_index("datetime_utc", inplace=True)
    df.drop(columns=["timestamp"], inplace=True)  # Remove numeric timestamp column

    # Sort by time to ensure sequential order
    df.sort_index(inplace=True)

    return df


class BacktestDataPreparer:
    """Prepare and transform data for backtesting purposes."""

    def __init__(
        self,
        backtest_report_service: BacktestReportService,
        metadata_service: APIMetadataService,
        prices_service: APIPricesService,
    ):
        """Initialize backtest data preparer with required services.

        Args:
            backtest_report_service (BacktestReportService): Service for accessing backtest reports
            metadata_service (APIMetadataService): Service for accessing metadata
            prices_service (APIPricesService): Service for accessing price data
        """
        self.backtest_report_service = backtest_report_service
        self.metadata_service = metadata_service
        self.prices_service = prices_service

    def get_daily_ohlcv_for_ticker(
        self, ticker: str, limit: int = 2000
    ) -> pd.DataFrame:
        """Get and convert daily price data for a single ticker.

        Args:
            ticker (str): Stock ticker symbol
            limit (int, optional): Maximum number of records to retrieve. Defaults to 2000.

        Returns:
            pd.DataFrame: DataFrame with OHLCV data
        """
        logger.info(f"Preparing daily OHLCV for ticker '{ticker}'...")
        res = self.prices_service.get_daily_prices(ticker, limit=limit, skip=0)
        json_res = res.model_dump()
        if not json_res:
            logger.warn("Null response. Return empty DF.")
            return pd.DataFrame()

        try:
            df = transform_single_ticker_response(json_res)
            return df
        except ValueError as e:
            logger.err(f"Could not process a response. Error: {e}. Skipping.")
            return pd.DataFrame()

    def get_backtest_report(self, ticker: str, backtest_date: datetime):
        """Get a specific backtest report for a ticker and date.

        Args:
            ticker (str): Stock ticker symbol
            backtest_date (datetime): Date for which to retrieve the report

        Returns:
            Report object for the specified ticker and date

        Raises:
            ValueError: If no report is found for the ticker and date
        """
        report = self.backtest_report_service.get_backtest_report(ticker, backtest_date)
        if report is None:
            raise ValueError(
                "No report found for ticker: {}, backtest_date: {}".format(
                    ticker, backtest_date
                )
            )
        return report

    def get_backtest_reports_for_ticker(self, ticker: str):
        """Get all backtest reports for a specific ticker.

        Args:
            ticker (str): Stock ticker symbol

        Returns:
            List of all backtest reports for the ticker
        """
        return self.backtest_report_service.get_all_backtest_reports(ticker)

    def get_all_tickers(self) -> list[str]:
        """Get a list of all available tickers.

        Returns:
            list[str]: List of all available tickers in uppercase
        """
        return [x.upper() for x in self.metadata_service.metadata_cache.keys()]
