# Open main.py file

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from . import dependencies # Import module dependencies
from .core import config as cfg
from app.api.v1.endpoints import root

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.
    
    Args:
        app (FastAPI): The FastAPI application instance
    """
    # 1. Initialize all dependencies
    dependencies.create_dependencies()
    
    # 2. Get the initialized manager to run background tasks
    manager = dependencies.get_backtest_context_manager()
    if cfg.EVO_REGEN_BACKTEST_DATA:
        asyncio.create_task(manager.prepare_all_contexts())
    
    yield
    
    # 3. Cleanup on shutdown
    dependencies.close_dependencies()

app = FastAPI(
    title='Evo-worker of ITAPIA',
    lifespan=lifespan
)

app.include_router(root.router, prefix=cfg.EVO_WORKER_V1_BASE_ROUTE, tags=['Root'])