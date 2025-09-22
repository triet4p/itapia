# Create file app/dependencies.py

from typing import Optional

from itapia_common.dblib.services import (
    APIMetadataService,
    APIPricesService,
    BacktestReportService,
)
from itapia_common.dblib.session import get_rdbms_session

from .backtest.context import BacktestContextManager
from .backtest.data_prepare import BacktestDataPreparer

# Global variable "protected" by underscore, only accessed through getter functions
_backtest_context_manager: Optional[BacktestContextManager] = None


def create_dependencies():
    """Factory function called ONLY ONCE in lifespan to initialize all objects."""
    global _backtest_context_manager

    # Only initialize if not already done
    if _backtest_context_manager is not None:
        return

    # DB and services initialization logic
    db_session_gen = get_rdbms_session()
    db = next(db_session_gen)
    # This initialization logic can cause errors if DB connection fails
    # Should be wrapped in try...finally to ensure sessions are closed
    try:
        metadata_service = APIMetadataService(rdbms_session=db)
        prices_service = APIPricesService(
            rdbms_session=db, metadata_service=metadata_service, redis_client=None
        )
        backtest_report_service = BacktestReportService(rdbms_session=db)

        backtest_data_preparer = BacktestDataPreparer(
            prices_service=prices_service,
            backtest_report_service=backtest_report_service,
            metadata_service=metadata_service,
        )

        # Initialize and assign to global variable
        _backtest_context_manager = BacktestContextManager(
            data_preparer=backtest_data_preparer
        )
    finally:
        db.close()


def get_backtest_context_manager() -> BacktestContextManager:
    """FastAPI Dependency Injector function.

    Returns the instance created in lifespan.

    Returns:
        BacktestContextManager: The initialized backtest context manager

    Raises:
        RuntimeError: If BacktestContextManager has not been initialized
    """
    if _backtest_context_manager is None:
        raise RuntimeError(
            "BacktestContextManager has not been initialized. Check lifespan event."
        )
    return _backtest_context_manager


def close_dependencies():
    """Cleanup function called when the application shuts down."""
    global _backtest_context_manager
    _backtest_context_manager = None
