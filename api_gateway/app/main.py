# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from app.api.v1.endpoints import data_viewer, ai_quick_analysis, ai_quick_advisor, ai_rules
from app.clients.ai_quick_analysis import ai_quick_analysis_client
from app.clients.ai_quick_advisor import ai_quick_advisor_client
from app.clients.ai_rules import ai_rules_client
from app.core.config import GATEWAY_V1_BASE_ROUTE, GATEWAY_ALLOW_ORIGINS

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code này chạy khi ứng dụng khởi động
    # Tái sử dụng client để mở connection pool
    async with ai_quick_analysis_client:
        async with ai_quick_advisor_client:
            async with ai_rules_client:
                yield

app = FastAPI(
    title="ITAPIA API Service",
    description="API Gateway cho hệ thống ITAPIA, phục vụ dữ liệu và điều phối các tác vụ AI.",
    version="1.0.0"
)

# 2. Định nghĩa danh sách các "nguồn" (frontend) được phép truy cập
#    Đây là địa chỉ của ứng dụng Vue của bạn
origins = GATEWAY_ALLOW_ORIGINS

# 3. Thêm middleware vào ứng dụng FastAPI
#    ĐOẠN CODE NÀY PHẢI ĐƯỢC THÊM VÀO TRƯỚC KHI BẠN INCLUDE BẤT KỲ ROUTER NÀO
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Cho phép các nguồn trong danh sách `origins`
    allow_credentials=True, # Cho phép gửi cookie (quan trọng cho authentication sau này)
    allow_methods=["*"],    # Cho phép tất cả các phương thức (GET, POST, etc.)
    allow_headers=["*"],    # Cho phép tất cả các header
)

# Bao gồm router từ file data_viewer
app.include_router(data_viewer.router, prefix=GATEWAY_V1_BASE_ROUTE)
app.include_router(ai_quick_analysis.router, prefix=GATEWAY_V1_BASE_ROUTE)
app.include_router(ai_quick_advisor.router, prefix=GATEWAY_V1_BASE_ROUTE)
app.include_router(ai_rules.router, prefix=GATEWAY_V1_BASE_ROUTE)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to ITAPIA API Service"}