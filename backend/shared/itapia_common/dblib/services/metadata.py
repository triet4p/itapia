"""Service layer for metadata entities.

This module provides high-level interfaces for accessing ticker and sector metadata,
handling caching and conversion between raw data and Pydantic models.
"""

from typing import Any, Dict, List, Literal, Optional

from itapia_common.dblib.crud.metadata import get_all_sectors, get_ticker_metadata
from itapia_common.logger import ITAPIALogger
from itapia_common.schemas.entities.metadata import SectorMetadata, TickerMetadata
from sqlalchemy import Engine
from sqlalchemy.orm import Session

logger = ITAPIALogger("Metadata Service of DB")


class APIMetadataService:
    """Centralized service class for metadata-related API queries."""

    def __init__(self, rdbms_session: Optional[Session]):
        self.rdbms_session: Session = None
        self.metadata_cache: Dict[str, Any] = None

        if rdbms_session is not None:
            self.set_rdbms_session(rdbms_session)

    def set_rdbms_session(self, rdbms_session: Session):
        self.rdbms_session = rdbms_session
        self.metadata_cache = get_ticker_metadata(rdbms_connection=rdbms_session)

    def get_validate_ticker_info(
        self, ticker: str, data_type: Literal["daily", "intraday", "news"]
    ) -> TickerMetadata:
        """Get and validate ticker information for a specific data type.

        This method retrieves ticker metadata from cache and converts it to a Pydantic model.

        Args:
            ticker (str): The ticker symbol to retrieve information for.
            data_type (Literal['daily', 'intraday', 'news']): The type of data the ticker will be used for.

        Returns:
            TickerMetadata: The validated ticker metadata.

        Raises:
            ValueError: If the ticker is not found in the metadata cache.
        """
        if self.metadata_cache is None:
            raise ValueError("Metadata cache is missing, check the connection!")

        logger.info(f"SERVICE: Preparing ticker info metadata of ticker {ticker}...")
        ticker_info = self.metadata_cache.get(ticker.upper())
        if not ticker_info:
            raise ValueError(f"Ticker '{ticker}' not found.")
        ticker_info["ticker"] = ticker
        ticker_info["data_type"] = data_type
        return TickerMetadata(**ticker_info)

    def get_sector_code_of(self, ticker: str) -> str:
        """Get the sector code for a given ticker.

        Args:
            ticker (str): The ticker symbol to retrieve the sector code for.

        Returns:
            str: The sector code for the ticker.

        Raises:
            ValueError: If the ticker is not found or has no sector code.
        """
        if self.metadata_cache is None:
            raise ValueError("Metadata cache is missing, check the connection!")
        logger.info(f"SERVICE: Get sector code of a ticker")
        ticker_info = self.metadata_cache.get(ticker.upper())
        if not ticker_info:
            raise ValueError(f"Ticker '{ticker}' not found.")
        sector_code = ticker_info.get("sector_code")
        if sector_code is None:
            raise ValueError(f"Missing sector for ticker {ticker}")
        return sector_code

    def get_all_sectors(self) -> List[SectorMetadata]:
        """Get a list of all supported sectors.

        Returns:
            List[SectorMetadata]: A list of sector metadata objects.
        """
        if self.rdbms_session is None:
            raise ValueError("Connection is empty!!")
        logger.info("SERVICE: Preparing all sectors...")
        sector_rows = get_all_sectors(
            self.rdbms_session
        )  # Assuming metadata_crud.py file exists

        # Convert raw results to a list of Pydantic objects
        return [SectorMetadata(**row) for row in sector_rows]


class DataMetadataService:
    """Service class for data-level metadata operations."""

    def __init__(self, engine: Engine):
        self.metadata_cache = get_ticker_metadata(rdbms_engine=engine)

    def get_all_tickers(self) -> list[str]:
        """Get a list of all ticker symbols.

        Returns:
            list[str]: A list of all ticker symbols.
        """
        return list(self.metadata_cache.keys())
