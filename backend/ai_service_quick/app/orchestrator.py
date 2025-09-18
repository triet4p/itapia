"""AI Service Quick Orchestrator - Top-level coordinator for the application.

This module implements the CEO Orchestrator pattern, responsible for coordinating
the "Deputy CEOs" (Analysis and Advisor) to execute complete business processes.
"""

import asyncio
from datetime import datetime
from typing import Dict, Literal
import uuid

from itapia_common.schemas.entities.personal import QuantitivePreferencesConfig
from itapia_common.schemas.entities.profiles import ProfileEntity
from itapia_common.schemas.entities.rules import ExplainationRuleEntity, NodeType, SemanticType

from .analysis import AnalysisOrchestrator
from .advisor import AdvisorOrchestrator
from .analysis.explainer.orchestrator import ExplainReportType
from .rules import RulesOrchestrator
from .personal import PersonalAnalysisOrchestrator
from itapia_common.logger import ITAPIALogger

# Import required schemas for proper type hinting
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from itapia_common.schemas.entities.analysis.technical import TechnicalReport
from itapia_common.schemas.entities.analysis.news import NewsAnalysisReport
from itapia_common.schemas.entities.analysis.forecasting import ForecastingReport
from itapia_common.schemas.entities.advisor import AdvisorReportSchema
from itapia_common.schemas.entities.backtest import BACKTEST_GENERATION_STATUS

logger = ITAPIALogger('AI Quick Orchestrator')


class AIServiceQuickOrchestrator:
    """CEO Orchestrator - Highest level.
    
    Responsible for coordinating the "Deputy CEOs" (Analysis and Advisor).
    """
    
    def __init__(self, analysis_orchestrator: AnalysisOrchestrator, advisor_orchestrator: AdvisorOrchestrator,
                 rule_orchestrator: RulesOrchestrator, personal_orchestrator: PersonalAnalysisOrchestrator):
        """Initialize the CEO Orchestrator with required deputy orchestrators.
        
        Args:
            analysis_orchestrator (AnalysisOrchestrator): Analysis deputy orchestrator
            advisor_orchestrator (AdvisorOrchestrator): Advisor deputy orchestrator
            rule_orchestrator (RulesOrchestrator): Rules orchestrator
            personal_orchestrator (PersonalAnalysisOrchestrator): Personal analysis orchestrator
        """
        self.analysis = analysis_orchestrator
        self.advisor = advisor_orchestrator
        self.rules = rule_orchestrator
        self.personal = personal_orchestrator
        self.success_event = asyncio.Event()
        self.backtest_jobs_status: Dict[str, BACKTEST_GENERATION_STATUS] = {}
        logger.info("CEO Orchestrator initialized with Analysis and Advisor deputies.")

    # === DELEGATE METHODS FOR ANALYSIS ORCHESTRATOR ===
    # These methods simply delegate to the Analysis "Deputy CEO".
    # This keeps API endpoints unchanged.

    async def get_technical_report(self, ticker: str,
                                   daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                                   required_type: Literal['daily', 'intraday', 'all']='all'
                                   ) -> TechnicalReport:
        """Get technical analysis report by delegating to Analysis orchestrator.
        
        Args:
            ticker (str): Stock ticker symbol
            daily_analysis_type (Literal['short', 'medium', 'long'], optional): Daily analysis type. 
                Defaults to 'medium'.
            required_type (Literal['daily', 'intraday', 'all'], optional): Required analysis type. 
                Defaults to 'all'.
                
        Returns:
            TechnicalReport: Technical analysis report
        """
        return await self.analysis.get_technical_report(ticker, daily_analysis_type, required_type)

    async def get_forecasting_report(self, ticker: str) -> ForecastingReport:
        """Get forecasting report by delegating to Analysis orchestrator.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            ForecastingReport: Forecasting report
        """
        return await self.analysis.get_forecasting_report(ticker)

    async def get_news_report(self, ticker: str) -> NewsAnalysisReport:
        """Get news analysis report by delegating to Analysis orchestrator.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            NewsAnalysisReport: News analysis report
        """
        return await self.analysis.get_news_report(ticker)
        
    async def get_full_analysis_report(self, ticker: str, 
                                       daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
                                       required_type: Literal['daily', 'intraday', 'all']='all'
                                      ) -> QuickCheckAnalysisReport:
        """Get complete analysis report by delegating to Analysis orchestrator.
        
        Args:
            ticker (str): Stock ticker symbol
            daily_analysis_type (Literal['short', 'medium', 'long'], optional): Daily analysis type. 
                Defaults to 'medium'.
            required_type (Literal['daily', 'intraday', 'all'], optional): Required analysis type. 
                Defaults to 'all'.
                
        Returns:
            QuickCheckAnalysisReport: Complete analysis report
        """
        return await self.analysis.get_full_analysis_report(ticker, daily_analysis_type,
                                                            required_type)
        
    async def get_full_analysis_explaination_report(
        self, 
        ticker: str, 
        daily_analysis_type: Literal['short', 'medium', 'long'] = 'medium',
        required_type: Literal['daily', 'intraday', 'all']='all',
        explain_type: ExplainReportType = 'all'
    ) -> str:
        """Get complete analysis explanation report by delegating to Analysis orchestrator.
        
        Args:
            ticker (str): Stock ticker symbol
            daily_analysis_type (Literal['short', 'medium', 'long'], optional): Daily analysis type. 
                Defaults to 'medium'.
            required_type (Literal['daily', 'intraday', 'all'], optional): Required analysis type. 
                Defaults to 'all'.
            explain_type (ExplainReportType, optional): Explanation report type. 
                Defaults to 'all'.
                
        Returns:
            str: Complete analysis explanation report
        """
        # This function may need reconsideration since Advisor is now available
        # Temporarily still calls the Analysis explainer
        return await self.analysis.get_full_explaination_report(ticker, daily_analysis_type,
                                                               required_type, explain_type)

    # === NEW BUSINESS METHODS FOR ADVISOR ===

    async def get_full_advisor_report(self, ticker: str,
                                      quantitive_config: QuantitivePreferencesConfig,
                                      limit: int = 10) -> AdvisorReportSchema:
        """Complete business process: Analysis -> Advice.
        
        Executes the complete workflow from analysis to advisor recommendations.
        
        Args:
            ticker (str): Stock ticker symbol
            user_id (str): User identifier for personalization
            
        Returns:
            AdvisorReportSchema: Complete advisor report
        """
        logger.info(f"CEO -> Initiating full ADVISOR workflow for '{ticker}'...")
        
        # 1. Call Analysis "Deputy CEO" to get analysis report
        analysis_report = await self.analysis.get_full_analysis_report(
            ticker, 'medium', 'all'
        )
        
        decision_all_rules = await self.rules.get_ready_rules(purpose=SemanticType.DECISION_SIGNAL)
        risk_all_rules = await self.rules.get_ready_rules(purpose=SemanticType.RISK_LEVEL)
        oppor_all_rules = await self.rules.get_ready_rules(purpose=SemanticType.OPPORTUNITY_RATING)
        
        decision_selected_rules = self.personal.filter_rules(decision_all_rules,
                                                             quantitive_config=quantitive_config,
                                                             limit=limit)
        
        risk_selected_rules = self.personal.filter_rules(risk_all_rules, 
                                                         quantitive_config=quantitive_config,
                                                         limit=limit)
        oppor_selected_rules = self.personal.filter_rules(oppor_all_rules, 
                                                          quantitive_config=quantitive_config,
                                                          limit=limit)
        
        # (personal_rules will be used later)

        # Stage 3: Execute rules in parallel
        decision_task = self.rules.run_for_purpose(analysis_report, SemanticType.DECISION_SIGNAL, decision_selected_rules)
        risk_task = self.rules.run_for_purpose(analysis_report, SemanticType.RISK_LEVEL, risk_selected_rules)
        opp_task = self.rules.run_for_purpose(analysis_report, SemanticType.OPPORTUNITY_RATING, oppor_selected_rules)
        
        decision_results, risk_results, opp_results = await asyncio.gather(decision_task, risk_task, opp_task)

        
        # 2. Give that report to the Advisor "Deputy CEO" to get advice
        advisor_report = await self.advisor.get_advisor_report(analysis_report,
                                                               decision_results,
                                                               risk_results,
                                                               opp_results,
                                                               behavior_modifiers=quantitive_config.modifiers,
                                                               action_mapper=self.advisor.default_action_mapper)
        
        return advisor_report
    
    async def get_full_advisor_explaination_report(self, ticker: str,
                                      quantitive_config: QuantitivePreferencesConfig,
                                      limit: int = 10) -> str:
        """Get complete advisor explanation report.
        
        Args:
            ticker (str): Stock ticker symbol
            user_id (str): User identifier for personalization
            
        Returns:
            str: Complete advisor explanation report
        """
        analysis_report = await self.analysis.get_full_analysis_report(
            ticker, 'medium', 'all'
        )
        
        decision_all_rules = await self.rules.get_ready_rules(purpose=SemanticType.DECISION_SIGNAL)
        risk_all_rules = await self.rules.get_ready_rules(purpose=SemanticType.RISK_LEVEL)
        oppor_all_rules = await self.rules.get_ready_rules(purpose=SemanticType.OPPORTUNITY_RATING)
        
        decision_selected_rules = self.personal.filter_rules(decision_all_rules,
                                                             quantitive_config=quantitive_config,
                                                             limit=limit)
        risk_selected_rules = self.personal.filter_rules(risk_all_rules, 
                                                         quantitive_config=quantitive_config,
                                                         limit=limit)
        oppor_selected_rules = self.personal.filter_rules(oppor_all_rules, 
                                                          quantitive_config=quantitive_config,
                                                          limit=limit)
        
        # (personal_rules will be used later)

        # Stage 3: Execute rules in parallel
        decision_task = self.rules.run_for_purpose(analysis_report, SemanticType.DECISION_SIGNAL, decision_selected_rules)
        risk_task = self.rules.run_for_purpose(analysis_report, SemanticType.RISK_LEVEL, risk_selected_rules)
        opp_task = self.rules.run_for_purpose(analysis_report, SemanticType.OPPORTUNITY_RATING, oppor_selected_rules)
        
        decision_results, risk_results, opp_results = await asyncio.gather(decision_task, risk_task, opp_task)
        return await self.advisor.get_full_explaination_report(analysis_report,
                                                               decision_results,
                                                               risk_results,
                                                               opp_results,
                                                               behavior_modifiers=quantitive_config.modifiers)
    
    async def get_single_explaination_rule(self, rule_id: str) -> ExplainationRuleEntity:
        """Get explanation for a single rule.
        
        Args:
            rule_id (str): Rule identifier
            
        Returns:
            ExplainationRuleEntity: Rule explanation entity
        """
        return await self.rules.get_explaination_for_single_rule(rule_id)
    
    async def get_ready_rules(self, purpose: SemanticType) -> list:
        """Get all ready rules for a specific purpose.
        
        Args:
            purpose (SemanticType): Semantic purpose to filter rules by
            
        Returns:
            list: List of ready rules
        """
        return await self.rules.get_ready_rules(purpose)
    
    def get_nodes(self, node_type: NodeType = NodeType.ANY, 
                        purpose: SemanticType = SemanticType.ANY) -> list:
        """Get nodes by type and purpose.
        
        Args:
            node_type (NodeType, optional): Node type to filter by. Defaults to NodeType.ANY.
            purpose (SemanticType, optional): Semantic purpose to filter by. 
                Defaults to SemanticType.ANY.
                
        Returns:
            list: List of nodes matching criteria
        """
        return self.rules.get_nodes(node_type, purpose)
        
    async def preload_all_caches(self) -> None:
        """Start all background processes in parallel.
        
        Currently only the Analysis Orchestrator has preload processes.
        """
        # Currently only Analysis Orchestrator has preload processes
        try:
            await self.analysis.preload_all_caches()
        finally:
            logger.info("CEO -> Preloading all caches finished.")
            self.success_event.set()
        
    async def generate_backtest_reports(self, job_id: str, ticker: str, backtest_dates: list[datetime]) -> None:
        """Generate backtest reports for specific ticker and dates.
        
        Args:
            job_id (str): Unique identifier for the backtest job
            ticker (str): Stock ticker symbol
            backtest_dates (list[datetime]): List of dates for backtesting
        """
        self.backtest_jobs_status[job_id] = 'IDLE'
        logger.info(f"Backtest job '{job_id}' for ticker '{ticker}' set to IDLE.")
        
        try:
            # 2. Wait for cache preload to complete
            logger.info('Waiting for preload caches to complete...')
            await self.success_event.wait()
            logger.info('Preload caches finished, proceeding with backtest data generation.')
            
            self.backtest_jobs_status[job_id] = 'RUNNING'
            logger.info(f"Backtest job '{job_id}' for ticker '{ticker}' set to RUNNING.")

            await self.analysis.generate_backtest_data(
                ticker=ticker,
                backtest_dates=backtest_dates
            )
            
            # 4. If completed without errors, set status to COMPLETED
            self.backtest_jobs_status[job_id] = 'COMPLETED'
            logger.info(f"Backtest job '{job_id}' for ticker '{ticker}' set to COMPLETED.")

        except Exception as e:
            # 5. If error occurs, set status to FAILED
            logger.err(f"Backtest generation failed: {e}")
            self.backtest_jobs_status[job_id] = 'FAILED'
            # Re-raise error so background task can record it if needed
            raise
        
    def get_suggest_config(self, profile: ProfileEntity) -> QuantitivePreferencesConfig:
        return self.personal.get_suggest_config(profile)