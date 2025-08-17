# Mở file app/dependencies.py và thay thế toàn bộ nội dung

from typing import Optional

# Import tất cả các class cần thiết để khởi tạo
from .orchestrator import AIServiceQuickOrchestrator
from .analysis import AnalysisOrchestrator
from .advisor import AdvisorOrchestrator
from .analysis.technical import TechnicalOrchestrator
from .analysis.news import NewsOrchestrator
from .analysis.forecasting import ForecastingOrchestrator
from .advisor.aggeration import AggregationOrchestrator
from .rules import RulesOrchestrator
from .rules.explainer import RuleExplainerOrchestrator
from .personal import PersonalAnalysisOrchestrator
from .analysis.data_prepare import DataPrepareOrchestrator
from .analysis.explainer import AnalysisExplainerOrchestrator
from .advisor.explainer import AdvisorExplainerOrchestrator
from .analysis.backtest import BacktestOrchestrator
# (BacktestOrchestrator không còn cần thiết trong luồng chính của AI Quick nữa, có thể bỏ qua)

from itapia_common.dblib.session import get_rdbms_session, get_redis_connection
from itapia_common.dblib.services import (
    APIMetadataService, APIPricesService, APINewsService, RuleService, BacktestReportService
)

# Biến global được "bảo vệ", chỉ được truy cập qua các hàm getter
_ceo_orchestrator: Optional[AIServiceQuickOrchestrator] = None

def create_dependencies():
    """
    Hàm "nhà máy" này được gọi MỘT LẦN DUY NHẤT trong lifespan để khởi tạo tất cả các đối tượng.
    """
    global _ceo_orchestrator
    
    if _ceo_orchestrator is not None:
        return

    db_session_gen = get_rdbms_session()
    redis_gen = get_redis_connection()
    db = next(db_session_gen)
    redis = next(redis_gen)
    
    try:
        # 1. Khởi tạo các service cấp thấp
        metadata_service = APIMetadataService(rdbms_session=db)
        prices_service = APIPricesService(rdbms_session=db, redis_client=redis, metadata_service=metadata_service)
        news_service = APINewsService(rdbms_session=db, metadata_service=metadata_service)
        rule_service = RuleService(db_session=db)
        backtest_report_service = BacktestReportService(db_session=db)

        # 2. Khởi tạo các orchestrator cấp "trưởng phòng"
        data_prepare_orc = DataPrepareOrchestrator(metadata_service, prices_service, news_service)
        technical_orc = TechnicalOrchestrator()
        news_orc = NewsOrchestrator()
        forecasting_orc = ForecastingOrchestrator()
        analysis_explaine_orc = AnalysisExplainerOrchestrator()
        aggeration_orc = AggregationOrchestrator()
        advisor_explainer_orc = AdvisorExplainerOrchestrator()
        rule_explainer = RuleExplainerOrchestrator()
        personal_orc = PersonalAnalysisOrchestrator()
        backtest_orc = BacktestOrchestrator(backtest_report_service)
        
        # 3. Khởi tạo các orchestrator cấp "phó CEO"
        analysis_orc = AnalysisOrchestrator(
            data_preparer=data_prepare_orc,
            tech_analyzer=technical_orc,
            forecaster=forecasting_orc,
            news_analyzer=news_orc,
            explainer=analysis_explaine_orc,
            backtest_orchestrator=backtest_orc
            # backtest_orchestrator không còn cần thiết cho luồng chính, nhưng nếu cần thì khởi tạo ở đây
        )
        advisor_orc = AdvisorOrchestrator(agg_orc=aggeration_orc, explainer=advisor_explainer_orc)
        rule_orc = RulesOrchestrator(rule_service, explainer=rule_explainer)
        
        # 4. Khởi tạo "CEO" và gán vào biến global
        _ceo_orchestrator = AIServiceQuickOrchestrator(
            analysis_orchestrator=analysis_orc,
            advisor_orchestrator=advisor_orc,
            rule_orchestrator=rule_orc,
            personal_orchestrator=personal_orc
        )
    finally:
        db.close()
        redis.close()

def get_ceo_orchestrator() -> AIServiceQuickOrchestrator:
    """
    Hàm Dependency Injector cho FastAPI.
    Trả về instance singleton của "CEO" Orchestrator.
    """
    if _ceo_orchestrator is None:
        raise RuntimeError("AIServiceQuickOrchestrator has not been initialized. Check lifespan event.")
    return _ceo_orchestrator

def close_dependencies():
    """Hàm dọn dẹp, được gọi khi ứng dụng tắt."""
    global _ceo_orchestrator
    _ceo_orchestrator = None