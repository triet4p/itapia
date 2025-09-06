"""Main application module for the AI Service Quick API.

This module sets up the FastAPI application, configures lifespan management,
and registers all API routes.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from . import dependencies  # <-- Import factory module
from .api.v1.endpoints import quick_analysis, quick_advisor, rules, backtest, root
from .core.config import AI_QUICK_V1_BASE_ROUTE


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: initialize on startup and cleanup on shutdown.
    
    This context manager handles the complete application lifecycle, including:
    1. Initializing all dependencies through the factory pattern
    2. Scheduling background tasks like cache preloading
    3. Cleaning up resources on application shutdown
    
    Args:
        app (FastAPI): The FastAPI application instance
    """
    print("AI Service starting up... Initializing dependencies via factory.")
    # 1. Initialize all dependencies
    dependencies.create_dependencies()
    
    # 2. Get the initialized orchestrator to run background tasks
    orchestrator = dependencies.get_ceo_orchestrator()
    print("Scheduling pre-warming task to run in the background...")
    asyncio.create_task(orchestrator.preload_all_caches())
            
    yield
    
    # 3. Cleanup on shutdown
    print("AI Service shutting down. Cleaning up dependencies.")
    dependencies.close_dependencies()


app = FastAPI(
    title="ITAPIA AI Service Quick",
    description="Internal API for the AI Service quick analysis process",
    version="1.0.0",
    lifespan=lifespan
)

# Include all routers
app.include_router(quick_analysis.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Quick Analysis"])
app.include_router(quick_advisor.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Quick Advisor"])
app.include_router(rules.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Rules"])
app.include_router(backtest.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["Backtest Generation"])
app.include_router(root.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=['Root'])