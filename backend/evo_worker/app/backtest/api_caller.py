from typing import List
import httpx

from app.core.config import AI_SERVICE_QUICK_BASE_URL
from app.core.exceptions import BacktestError

# Giả định các schema này tồn tại trong shared_lib và đã được cập nhật
from itapia_common.schemas.api.backtest import (
    BacktestGenerationRequest,
    BacktestGenerationCheckResponse
)

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Backtest API Caller')

# Khởi tạo một HTTP client riêng cho các tác vụ liên quan đến backtest
# Tăng timeout vì tác vụ khởi tạo có thể mất một chút thời gian
backtest_api_client = httpx.AsyncClient(base_url=AI_SERVICE_QUICK_BASE_URL, timeout=30.0)

async def trigger_backtest_generation_task(ticker: str, timestamps: List[int]) -> BacktestGenerationCheckResponse:
    """
    Gửi yêu cầu POST đến AI Service Quick để bắt đầu tác vụ tạo dữ liệu backtest.

    Args:
        timestamps (List[int]): Danh sách các Unix timestamps cho các ngày cần tạo báo cáo.

    Returns:
        BacktestGenerationCheckResponse: Phản hồi từ server, thường chứa trạng thái 'RUNNING'.
    
    Raises:
        HTTPException: Nếu API trả về lỗi hoặc không thể kết nối.
    """
    try:
        # 1. Chuẩn bị payload theo schema
        request_payload = BacktestGenerationRequest(ticker=ticker, backtest_dates_ts=timestamps)
        
        # 2. Gửi yêu cầu POST
        logger.info(f'POST to url {backtest_api_client.base_url}/backtest/generate')
        response = await backtest_api_client.post(
            "/backtest/generate",
            json=request_payload.model_dump()
        )
        
        # 3. Kiểm tra lỗi và parse response
        response.raise_for_status()
        return BacktestGenerationCheckResponse.model_validate(response.json())

    except httpx.HTTPStatusError as e:
        # Xử lý các lỗi HTTP (ví dụ: 409 Conflict, 500 Internal Server Error)
        detail = e.response.json().get("detail", "Unknown error from AI Service")
        logger.err(detail)
        raise BacktestError(msg=detail)
        
    except httpx.RequestError as e:
        # Xử lý các lỗi kết nối (ví dụ: không thể kết nối đến service)
        logger.err(f"AI Service is unavailable: {type(e).__name__}")
        raise BacktestError(msg=f"AI Service is unavailable: {type(e).__name__}")


async def check_backtest_generation_status(job_id: str) -> BacktestGenerationCheckResponse:
    """
    Gửi yêu cầu GET để kiểm tra trạng thái của tác vụ tạo dữ liệu backtest.

    Returns:
        BacktestGenerationCheckResponse: Phản hồi từ server chứa trạng thái hiện tại.
    
    Raises:
        HTTPException: Nếu API trả về lỗi hoặc không thể kết nối.
    """
    try:
        # 1. Gửi yêu cầu GET
        logger.info(f'GET from url {backtest_api_client.base_url}/backtest/check/{job_id}')
        response = await backtest_api_client.get(f"/backtest/check/{job_id}")
        
        # 2. Kiểm tra lỗi và parse response
        response.raise_for_status()
        return BacktestGenerationCheckResponse.model_validate(response.json())

    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", "Unknown error from AI Service")
        logger.err(detail)
        raise BacktestError(msg=detail)
        
    except httpx.RequestError as e:
        # Xử lý các lỗi kết nối (ví dụ: không thể kết nối đến service)
        logger.err(f"AI Service is unavailable: {type(e).__name__}")
        raise BacktestError(msg=f"AI Service is unavailable: {type(e).__name__}")