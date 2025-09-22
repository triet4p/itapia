import asyncio
import uuid
from datetime import datetime, timezone

from app.dependencies import get_ceo_orchestrator
from app.orchestrator import AIServiceQuickOrchestrator
from fastapi import APIRouter, Depends, HTTPException, status
from itapia_common.schemas.api.backtest import (
    BacktestGenerationCheckResponse,
    BacktestGenerationRequest,
)

router = APIRouter()


@router.post(
    "/backtest/generate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start the backtest data generation process for specific dates",
    response_model=BacktestGenerationCheckResponse,
)
async def generate_backtest(
    req: BacktestGenerationRequest,
    orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
):
    job_id = uuid.uuid4().hex
    if orchestrator.backtest_jobs_status.get(job_id, "IDLE") == "RUNNING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Backtest generation is already running",
        )

    backtest_dates_ts = req.backtest_dates_ts
    backtest_dates = [
        datetime.fromtimestamp(ts, tz=timezone.utc) for ts in backtest_dates_ts
    ]

    orchestrator.backtest_jobs_status[job_id] = "IDLE"
    asyncio.create_task(
        orchestrator.generate_backtest_reports(job_id, req.ticker, backtest_dates)
    )

    return BacktestGenerationCheckResponse(job_id=job_id, status="IDLE")


@router.get(
    "/backtest/check/{job_id}",
    response_model=BacktestGenerationCheckResponse,
    summary="Get the current status of the backtest data generation process",
)
async def check_backtest(
    job_id: str,
    orchestrator: AIServiceQuickOrchestrator = Depends(get_ceo_orchestrator),
):
    job_status = orchestrator.backtest_jobs_status.get(job_id)

    if job_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job ID '{job_id}' not found.",
        )
    return BacktestGenerationCheckResponse(job_id=job_id, status=job_status)
