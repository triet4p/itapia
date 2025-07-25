import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.endpoints import quick_analysis
from app.core.config import AI_QUICK_V1_BASE_ROUTE
from app.orchestrator import AIServiceQuickOrchestrator

from itapia_common.dblib.session import get_rdbms_session, get_redis_connection
from itapia_common.dblib.services import APIMetadataService, APIPricesService, APINewsService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- KHỞI TẠO CÁC DỊCH VỤ CẤP THẤP ---
    print("AI Service starting up... Initializing dependencies.")
    # Tạo một session DB chỉ để dùng trong quá trình khởi tạo
    # Lưu ý: Các request sau này sẽ tạo session riêng.
    db_session_gen = get_rdbms_session()
    redis_gen = get_redis_connection()
    db = next(db_session_gen)
    redis = next(redis_gen)
    try:
        # Khởi tạo các service từ shared_library
        metadata_service = APIMetadataService(rdbms_session=db)
        prices_service = APIPricesService(rdbms_session=db, redis_client=redis, metadata_service=metadata_service)
        news_service = APINewsService(rdbms_session=db, metadata_service=metadata_service)
        
        # --- KHỞI TẠO "CEO" ORCHESTRATOR DUY NHẤT ---
        ceo = AIServiceQuickOrchestrator(
            metadata_service=metadata_service,
            prices_service=prices_service,
            news_service=news_service
        )
        # Gán vào state của app để các endpoint có thể truy cập
        app.state.ceo_orchestrator = ceo
    finally:
        db.close() # Đóng session đã dùng để khởi tạo
        redis.close()
    
    # --- CHẠY TÁC VỤ "LÀM NÓNG" Ở CHẾ ĐỘ NỀN ---
    print("Scheduling pre-warming task to run in the background...")
    asyncio.create_task(app.state.ceo_orchestrator.preload_all_caches())
    
    yield
    
    # --- Code dọn dẹp khi tắt ứng dụng (nếu cần) ---
    print("AI Service shutting down.")

app = FastAPI(
    title="ITAPIA AI Service Quick",
    description="API nội bộ cho quy trình phân tích nhanh của AI Service",
    version="1.0.0",
    lifespan=lifespan
)

app.state.orchestrator = None

# Bao gồm router từ file data_viewer
app.include_router(quick_analysis.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Quick"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to ITAPIA AI Quick Service"}