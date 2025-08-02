import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.endpoints import quick_analysis, quick_advisor, rules
from app.core.config import AI_QUICK_V1_BASE_ROUTE
from app.orchestrator import AIServiceQuickOrchestrator
from app.analysis import AnalysisOrchestrator
from app.advisor import AdvisorOrchestrator
from app.analysis.technical import TechnicalOrchestrator
from app.analysis.news import NewsOrchestrator
from app.analysis.forecasting import ForecastingOrchestrator
from app.advisor.aggeration import AggregationOrchestrator
from app.rules import RulesOrchestrator
from app.rules.explainer import RuleExplainerOrchestrator
from app.personal import PersonalAnalysisOrchestrator
from app.data_prepare import DataPrepareOrchestrator
from app.analysis.explainer import AnalysisExplainerOrchestrator
from app.advisor.explainer import AdvisorExplainerOrchestrator

from itapia_common.dblib.session import get_rdbms_session, get_redis_connection
from itapia_common.dblib.services import APIMetadataService, APIPricesService, APINewsService, RuleService

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
        rule_service = RuleService(db_session=db)
        # --- KHỞI TẠO CÁC TRƯỞNG PHÒNG VÀ PHÓ CEO CHẮC CHẮN PHẢI TỒN TẠI ---
        
        data_prepare_orc = DataPrepareOrchestrator(
            metadata_service=metadata_service,
            prices_service=prices_service,
            news_service=news_service
        )
        
        technical_orc = TechnicalOrchestrator()
        news_orc = NewsOrchestrator()
        forecasting_orc = ForecastingOrchestrator()
        
        analysis_explaine_orc = AnalysisExplainerOrchestrator()
        
        analysis_orc = AnalysisOrchestrator(
            data_preparer=data_prepare_orc,
            tech_analyzer=technical_orc,
            forecaster=forecasting_orc,
            news_analyzer=news_orc,
            explainer=analysis_explaine_orc
        )
        
        aggeration_orc = AggregationOrchestrator()
        advisor_explainer_orc = AdvisorExplainerOrchestrator()
        
        advisor_orc = AdvisorOrchestrator(
            agg_orc=aggeration_orc,
            explainer=advisor_explainer_orc
        )
        
        rule_explainer = RuleExplainerOrchestrator()
        
        rule_orc = RulesOrchestrator(rule_service, explainer=rule_explainer)
        personal_orc = PersonalAnalysisOrchestrator()
        
        ceo = AIServiceQuickOrchestrator(
            analysis_orchestrator=analysis_orc,
            advisor_orchestrator=advisor_orc,
            rule_orchestrator=rule_orc,
            personal_orchestrator=personal_orc
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
app.include_router(quick_analysis.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Quick Analysis"])
app.include_router(quick_advisor.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Quick Advisor"])
app.include_router(rules.router, prefix=AI_QUICK_V1_BASE_ROUTE, tags=["AI Rules"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to ITAPIA AI Quick Service"}