"""Provides FastAPI dependencies for database connections and services.

This module defines dependency injection functions for FastAPI that help manage
database connections and service instances in a clean and reusable way.
"""

from fastapi import Depends
from redis.client import Redis
from sqlalchemy.orm import Session

from .services import (
    APIMetadataService,
    APINewsService,
    APIPricesService,
    BacktestReportService,
)
from .session import get_rdbms_session, get_redis_connection


def get_metadata_service(
    rdbms_session: Session = Depends(get_rdbms_session),
) -> APIMetadataService:
    """Create and return an APIMetadataService instance.

    Args:
        rdbms_session (Session): Database session dependency.

    Returns:
        APIMetadataService: An instance of the metadata service.
    """
    return APIMetadataService(rdbms_session)


def get_prices_service(
    rdbms_session: Session = Depends(get_rdbms_session),
    redis_client: Redis = Depends(get_redis_connection),
    metadata_service: APIMetadataService = Depends(get_metadata_service),
) -> APIPricesService:
    """Create and return an APIPricesService instance.

    Args:
        rdbms_session (Session): Database session dependency.
        redis_client (Redis): Redis client dependency.
        metadata_service (APIMetadataService): Metadata service dependency.

    Returns:
        APIPricesService: An instance of the prices service.
    """
    return APIPricesService(rdbms_session, redis_client, metadata_service)


def get_news_service(
    rdbms_session: Session = Depends(get_rdbms_session),
    metadata_service: APIMetadataService = Depends(get_metadata_service),
) -> APINewsService:
    """Create and return an APINewsService instance.

    Args:
        rdbms_session (Session): Database session dependency.
        metadata_service (APIMetadataService): Metadata service dependency.

    Returns:
        APINewsService: An instance of the news service.
    """
    return APINewsService(rdbms_session, metadata_service)


def get_backtest_report_service(
    rdbms_session: Session = Depends(get_rdbms_session),
) -> BacktestReportService:
    """Create and return a BacktestReportService instance.

    Args:
        rdbms_session (Session): Database session dependency.

    Returns:
        BacktestReportService: An instance of the backtest report service.
    """
    return BacktestReportService(rdbms_session)
