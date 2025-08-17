# Mở file main.py

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from . import dependencies # Import module dependencies

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Khởi tạo tất cả dependencies
    dependencies.create_dependencies()
    
    # 2. Lấy manager đã được khởi tạo để chạy tác vụ nền
    manager = dependencies.get_backtest_context_manager()
    asyncio.create_task(manager.prepare_all_contexts())
    
    yield
    
    # 3. Dọn dẹp khi shutdown
    dependencies.close_dependencies()

app = FastAPI(
    title='Evo-worker of ITAPIA',
    lifespan=lifespan
)

# Thêm router
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to ITAPIA API Service"}