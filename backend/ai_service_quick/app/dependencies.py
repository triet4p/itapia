"""Dependency injection module for the AI Service Quick application.

This module handles the initialization and management of all application dependencies
following a factory pattern to create a singleton orchestrator instance.
"""

from typing import Optional

from app.personal.preferences import PreferencesManager
from app.personal.quantitive import QuantitivePreferencesAnalyzer
from app.personal.scorer import WeightedSumScorer
from itapia_common.dblib.services import (
    APIMetadataService,
    APINewsService,
    APIPricesService,
    BacktestReportService,
    RuleService,
)
from itapia_common.dblib.session import get_rdbms_session, get_redis_connection
from itapia_common.rules.action import MEDIUM_SWING_IDEAL_MAPPER

from .advisor import AdvisorOrchestrator
from .advisor.aggeration import AggregationOrchestrator
from .advisor.explainer import AdvisorExplainerOrchestrator
from .analysis import AnalysisOrchestrator
from .analysis.backtest import BacktestOrchestrator
from .analysis.data_prepare import DataPrepareOrchestrator
from .analysis.explainer import AnalysisExplainerOrchestrator
from .analysis.forecasting import ForecastingOrchestrator
from .analysis.news import NewsOrchestrator
from .analysis.technical import TechnicalOrchestrator

# Import all required classes for initialization
from .orchestrator import AIServiceQuickOrchestrator
from .personal import PersonalAnalysisOrchestrator
from .rules import RulesOrchestrator
from .rules.explainer import RuleExplainerOrchestrator

# (BacktestOrchestrator is no longer needed in the main AI Quick flow, can be ignored)


# Protected global variable, only accessible through getter functions
_ceo_orchestrator: Optional[AIServiceQuickOrchestrator] = None


def create_dependencies() -> None:
    """Factory function called ONCE during application startup to initialize all objects.

    This function creates all required services and orchestrators, building up the
    dependency tree from low-level services to high-level orchestrators, and finally
    creating the singleton CEO orchestrator instance.
    """
    global _ceo_orchestrator

    if _ceo_orchestrator is not None:
        return

    db_session_gen = get_rdbms_session()
    redis_gen = get_redis_connection()
    db = next(db_session_gen)
    redis = next(redis_gen)

    try:
        # 1. Initialize low-level services
        metadata_service = APIMetadataService(rdbms_session=db)
        prices_service = APIPricesService(
            rdbms_session=db, redis_client=redis, metadata_service=metadata_service
        )
        news_service = APINewsService(
            rdbms_session=db, metadata_service=metadata_service
        )
        rule_service = RuleService(rdbms_session=db)
        backtest_report_service = BacktestReportService(rdbms_session=db)

        # 2. Initialize "department head" level orchestrators
        data_prepare_orc = DataPrepareOrchestrator(
            metadata_service, prices_service, news_service
        )
        technical_orc = TechnicalOrchestrator()
        news_orc = NewsOrchestrator()
        forecasting_orc = ForecastingOrchestrator()
        analysis_explaine_orc = AnalysisExplainerOrchestrator()
        aggeration_orc = AggregationOrchestrator()
        advisor_explainer_orc = AdvisorExplainerOrchestrator()
        rule_explainer = RuleExplainerOrchestrator()
        personal_orc = PersonalAnalysisOrchestrator(
            quantitive_analyzer=QuantitivePreferencesAnalyzer(),
            preferences_manager=PreferencesManager(),
            scorer=WeightedSumScorer(),
        )
        backtest_orc = BacktestOrchestrator(backtest_report_service)

        # 3. Initialize "deputy CEO" level orchestrators
        analysis_orc = AnalysisOrchestrator(
            data_preparer=data_prepare_orc,
            tech_analyzer=technical_orc,
            forecaster=forecasting_orc,
            news_analyzer=news_orc,
            explainer=analysis_explaine_orc,
            backtest_orchestrator=backtest_orc,
            # backtest_orchestrator is no longer needed for main flow, but can be initialized here if needed
        )
        advisor_orc = AdvisorOrchestrator(
            agg_orc=aggeration_orc,
            explainer=advisor_explainer_orc,
            default_action_mapper=MEDIUM_SWING_IDEAL_MAPPER,
        )
        rule_orc = RulesOrchestrator(rule_service, explainer=rule_explainer)

        # 4. Initialize "CEO" and assign to global variable
        _ceo_orchestrator = AIServiceQuickOrchestrator(
            analysis_orchestrator=analysis_orc,
            advisor_orchestrator=advisor_orc,
            rule_orchestrator=rule_orc,
            personal_orchestrator=personal_orc,
        )
    finally:
        db.close()
        redis.close()


def get_ceo_orchestrator() -> AIServiceQuickOrchestrator:
    """FastAPI Dependency Injector.

    Returns the singleton instance of the "CEO" Orchestrator.

    Returns:
        AIServiceQuickOrchestrator: Singleton CEO orchestrator instance

    Raises:
        RuntimeError: If orchestrator has not been initialized
    """
    if _ceo_orchestrator is None:
        raise RuntimeError(
            "AIServiceQuickOrchestrator has not been initialized. Check lifespan event."
        )
    return _ceo_orchestrator


def close_dependencies() -> None:
    """Cleanup function called when application shuts down.

    Resets the global orchestrator instance to None.
    """
    global _ceo_orchestrator
    _ceo_orchestrator = None
