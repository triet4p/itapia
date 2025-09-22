"""API caller utilities for interacting with the AI Service Quick backtest endpoints."""

from typing import List

import httpx
from app.core.config import AI_SERVICE_QUICK_BASE_URL
from app.core.exceptions import BacktestError
from itapia_common.logger import ITAPIALogger

# Assume these schemas exist in shared_lib and have been updated
from itapia_common.schemas.api.backtest import (
    BacktestGenerationCheckResponse,
    BacktestGenerationRequest,
)

logger = ITAPIALogger("Backtest API Caller")

# Initialize a dedicated HTTP client for backtest-related tasks
# Increase timeout as initialization tasks may take some time
backtest_api_client = httpx.AsyncClient(
    base_url=AI_SERVICE_QUICK_BASE_URL, timeout=30.0
)


async def trigger_backtest_generation_task(
    ticker: str, timestamps: List[int]
) -> BacktestGenerationCheckResponse:
    """Send POST request to AI Service Quick to start backtest data generation task.

    Args:
        ticker (str): Stock ticker symbol
        timestamps (List[int]): List of Unix timestamps for dates needing reports

    Returns:
        BacktestGenerationCheckResponse: Server response, typically contains 'RUNNING' status

    Raises:
        HTTPException: If API returns error or cannot connect
    """
    try:
        # 1. Prepare payload according to schema
        request_payload = BacktestGenerationRequest(
            ticker=ticker, backtest_dates_ts=timestamps
        )

        # 2. Send POST request
        logger.info(f"POST to url {backtest_api_client.base_url}/backtest/generate")
        response = await backtest_api_client.post(
            "/backtest/generate", json=request_payload.model_dump()
        )

        # 3. Check for errors and parse response
        response.raise_for_status()
        return BacktestGenerationCheckResponse.model_validate(response.json())

    except httpx.HTTPStatusError as e:
        # Handle HTTP errors (e.g., 409 Conflict, 500 Internal Server Error)
        detail = e.response.json().get("detail", "Unknown error from AI Service")
        logger.err(detail)
        raise BacktestError(msg=detail)

    except httpx.RequestError as e:
        # Handle connection errors (e.g., cannot connect to service)
        logger.err(f"AI Service is unavailable: {type(e).__name__}")
        raise BacktestError(msg=f"AI Service is unavailable: {type(e).__name__}")


async def check_backtest_generation_status(
    job_id: str,
) -> BacktestGenerationCheckResponse:
    """Send GET request to check status of backtest data generation task.

    Args:
        job_id (str): Job ID to check status for

    Returns:
        BacktestGenerationCheckResponse: Server response containing current status

    Raises:
        HTTPException: If API returns error or cannot connect
    """
    try:
        # 1. Send GET request
        logger.info(
            f"GET from url {backtest_api_client.base_url}/backtest/check/{job_id}"
        )
        response = await backtest_api_client.get(f"/backtest/check/{job_id}")

        # 2. Check for errors and parse response
        response.raise_for_status()
        return BacktestGenerationCheckResponse.model_validate(response.json())

    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", "Unknown error from AI Service")
        logger.err(detail)
        raise BacktestError(msg=detail)

    except httpx.RequestError as e:
        # Handle connection errors (e.g., cannot connect to service)
        logger.err(f"AI Service is unavailable: {type(e).__name__}")
        raise BacktestError(msg=f"AI Service is unavailable: {type(e).__name__}")
