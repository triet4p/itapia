# Mở file app/main.py và thay thế toàn bộ nội dung

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from . import dependencies # <-- Import module nhà máy
from .api.v1.endpoints import quick_analysis, quick_advisor, rules, backtest
from .core.config import AI_QUICK_V1_BASE_ROUTE

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Quản lý vòng đời của ứng dụng: khởi tạo khi bắt đầu và dọn dẹp khi kết thúc.
    """
    print("AI Service starting up... Initializing dependencies via factory.")
    # 1. Khởi tạo tất cả dependencies
    dependencies.create_dependencies()
    
    # 2. Lấy orchestrator đã được khởi tạo để chạy tác vụ nền
    orchestrator = dependencies.get_ceo_orchestrator()
    print("Scheduling pre-warming task to run in the background...")
    asyncio.create_task(orchestrator.preload_all_caches())
            
    yield
    
    # 3. Dọn dẹp khi shutdown
    print("AI Service shutting down. Cleaning up dependencies.")
    dependencies.close_dependencies()

app = FastAPI(
    title="ITAPIA AI Service Quick",
    description="API nội bộ cho quy trình phân tích nhanh của AI Service",
    version="1.0.0",
    lifespan=lifespan
)

# Bao gồm tất cả các router
app.include_router(quick_analysis.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Quick Analysis"])
app.include_router(quick_advisor.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Quick Advisor"])
app.include_router(rules.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Rules"])
app.include_router(backtest.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["Backtest Generation"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to ITAPIA AI Quick Service"}