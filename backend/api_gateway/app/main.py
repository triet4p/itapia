# app/main.py
"""
Main application module for the ITAPIA API Gateway.

This module sets up the FastAPI application, configures CORS middleware,
includes all API routers, and manages the application lifecycle.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from app.api.v1.endpoints import data_viewer, ai_quick_analysis, ai_quick_advisor, ai_rules, \
    auth, users, profiles, root
from app.clients.ai_quick_analysis import ai_quick_analysis_client
from app.clients.ai_quick_advisor import ai_quick_advisor_client
from app.clients.ai_rules import ai_rules_client
from app.core.config import GATEWAY_V1_BASE_ROUTE, GATEWAY_ALLOW_ORIGINS

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    This function manages the application lifecycle, initializing and cleaning up
    resources when the application starts and stops.
    
    Args:
        app (FastAPI): The FastAPI application instance
    """
    # Code executed when the application starts
    # Reuse clients to open connection pools
    async with ai_quick_analysis_client:
        async with ai_quick_advisor_client:
            async with ai_rules_client:
                yield

app = FastAPI(
    title="ITAPIA API Service",
    description="API Gateway for the ITAPIA system, serving data and coordinating AI tasks.",
    version="1.0.0",
    lifespan=lifespan
)

# Define the list of allowed origins (frontend sources)
# This is the address of your Vue application
origins = GATEWAY_ALLOW_ORIGINS

# Add CORS middleware to the FastAPI application
# THIS CODE MUST BE ADDED BEFORE INCLUDING ANY ROUTERS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Allow origins in the `origins` list
    allow_credentials=True,     # Allow sending cookies (important for future authentication)
    allow_methods=["*"],        # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],        # Allow all headers
)

# Include routers from all endpoint modules
app.include_router(data_viewer.router, prefix=GATEWAY_V1_BASE_ROUTE)
app.include_router(ai_quick_analysis.router, prefix=GATEWAY_V1_BASE_ROUTE)
app.include_router(ai_quick_advisor.router, prefix=GATEWAY_V1_BASE_ROUTE)
app.include_router(ai_rules.router, prefix=GATEWAY_V1_BASE_ROUTE)
app.include_router(auth.router, prefix=GATEWAY_V1_BASE_ROUTE)
app.include_router(users.router, prefix=GATEWAY_V1_BASE_ROUTE)
app.include_router(profiles.router, prefix=GATEWAY_V1_BASE_ROUTE)
app.include_router(root.router)