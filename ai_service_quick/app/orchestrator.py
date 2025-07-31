# ai_service_quick/app/orchestrator.py
from typing import Literal

from .analysis.orchestrator import AnalysisOrchestrator
from .advisor.orchestrator import AdvisorOrchestrator
from .explainer.analysis.orchestrator import ExplainReportType, AnalysisExplainerOrchestrator
from itapia_common.logger import ITAPIALogger

# Import các schema cần thiết để có type hinting đúng
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from itapia_common.schemas.entities.analysis.technical import TechnicalReport
from itapia_common.schemas.entities.analysis.news import NewsAnalysisReport
from itapia_common.schemas.entities.analysis.forecasting import ForecastingReport
from itapia_common.schemas.entities.advisor import AdvisorReportSchema

logger = ITAPIALogger('AI Quick Orchestrator')

class AIServiceQuickOrchestrator:
    """
    CEO Orchestrator - Tầng cao nhất.
    Chịu trách nhiệm điều phối các "Phó CEO" (Analysis và Advisor).
    """
    def __init__(self, analysis_orchestrator: AnalysisOrchestrator, advisor_orchestrator: AdvisorOrchestrator):
        self.analysis = analysis_orchestrator
        self.advisor = advisor_orchestrator
        logger.info("CEO Orchestrator initialized with Analysis and Advisor deputies.")

    # === CÁC HÀM DELEGATE CHO ANALYSIS ORCHESTRATOR ===
    # Các hàm này chỉ đơn giản là gọi lại hàm của "Phó CEO" Analysis.
    # Điều này giữ cho các endpoint API không cần thay đổi.

    async def get_technical_report(self, ticker: str,
                                   daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                                   required_type: Literal['daily', 'intraday', 'all']='all'
                                   ) -> TechnicalReport:
        return await self.analysis.get_technical_report(ticker, daily_analysis_type, required_type)

    async def get_forecasting_report(self, ticker: str) -> ForecastingReport:
        return await self.analysis.get_forecasting_report(ticker)

    async def get_news_report(self, ticker: str) -> NewsAnalysisReport:
        return await self.analysis.get_news_report(ticker)
        
    async def get_full_analysis_report(self, ticker: str, 
                                       daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                                       required_type: Literal['daily', 'intraday', 'all']='all'
                                      ) -> QuickCheckAnalysisReport:
        return await self.analysis.get_full_analysis_report(ticker, daily_analysis_type,
                                                            required_type)
        
    async def get_full_analysis_explaination_report(
        self, 
        ticker: str, 
        daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
        required_type: Literal['daily', 'intraday', 'all']='all',
        explain_type: ExplainReportType = 'all'
    ) -> str:
        # Hàm này có thể cần được xem xét lại, vì giờ đây có cả Advisor
        # Tạm thời vẫn để nó gọi đến explainer của Analysis
        return await self.analysis.get_full_explanation_report(ticker, daily_analysis_type,
                                                               required_type, explain_type)

    # === HÀM NGHIỆP VỤ MỚI CHO ADVISOR ===

    async def get_full_advisor_report(self, ticker: str, 
                                      daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                                      required_type: Literal['daily', 'intraday', 'all']='all'
                                     ) -> AdvisorReportSchema:
        """
        Quy trình nghiệp vụ hoàn chỉnh: Phân tích -> Đưa ra lời khuyên.
        """
        logger.info(f"CEO -> Initiating full ADVISOR workflow for '{ticker}'...")
        
        # 1. Gọi "Phó CEO" Analysis để lấy báo cáo phân tích
        analysis_report = await self.analysis.get_full_analysis_report(
            ticker, daily_analysis_type, required_type
        )
        
        # 2. Đưa báo cáo đó cho "Phó CEO" Advisor để nhận lời khuyên
        advisor_report = await self.advisor.get_advisor_report(analysis_report)
        
        return advisor_report
        
    async def preload_all_caches(self):
        """Khởi động song song tất cả các quy trình nền."""
        # Hiện tại chỉ có Analysis Orchestrator có quy trình preload
        await self.analysis.preload_all_caches()