"""Advisor orchestrator for coordinating advice generation processes."""

import asyncio
from typing import Any, Callable, Dict, List, Tuple
from datetime import datetime, timezone

from itapia_common.schemas.entities.rules import SemanticType
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from itapia_common.schemas.entities.advisor import AdvisorReportSchema, FinalRecommendation, TriggeredRuleInfo
from itapia_common.logger import ITAPIALogger


from .aggeration import AggregationOrchestrator
from .explainer import AdvisorExplainerOrchestrator

logger = ITAPIALogger('Advisor Orchestrator')


class AdvisorOrchestrator:
    """Deputy CEO responsible for Providing Advice.
    
    Orchestrates department heads to create a complete advisory report.
    """
    
    def __init__(
        self, 
        agg_orc: AggregationOrchestrator,
        explainer: AdvisorExplainerOrchestrator
    ):
        """Initialize the advisor orchestrator with required components.
        
        Args:
            agg_orc (AggregationOrchestrator): Aggregation orchestrator instance
            explainer (AdvisorExplainerOrchestrator): Advisor explainer instance
        """
        self.agg_orc = agg_orc
        self.explainer = explainer
        logger.info("Advisor Orchestrator initialized with its department heads.")

    async def get_advisor_report(self, analysis_report: QuickCheckAnalysisReport, 
                                 decision_results: Tuple[List[float], List[TriggeredRuleInfo]],
                                 risk_results: Tuple[List[float], List[TriggeredRuleInfo]],
                                 opportunity_results: Tuple[List[float], List[TriggeredRuleInfo]],
                                 meta_weights: Dict[str, float]) -> AdvisorReportSchema:
        """Generate advisor report based on analysis results and rule evaluations.
        
        Args:
            analysis_report (QuickCheckAnalysisReport): Analysis report to base advice on
            decision_results (Tuple[List[float], List[TriggeredRuleInfo]]): Decision rule results
            risk_results (Tuple[List[float], List[TriggeredRuleInfo]]): Risk rule results
            opportunity_results (Tuple[List[float], List[TriggeredRuleInfo]]): Opportunity rule results
            meta_weights (Dict[str, float]): Meta-rule weights for final synthesis
            
        Returns:
            AdvisorReportSchema: Complete advisor report
        """
        logger.info(f"Advisor -> Generating advice for {analysis_report.ticker}...")
        
        # Unpack results
        (decision_scores, triggered_d) = decision_results
        (risk_scores, triggered_r) = risk_results
        (opportunity_scores, triggered_o) = opportunity_results

        # STEP 3: AGGREGATION (Synchronous)
        agg_scores = self.agg_orc.aggregate_raw_scores(decision_scores, risk_scores, opportunity_scores)
        final_scores = self.agg_orc.synthesize_final_decision(agg_scores, meta_weights)
        mapped_labels = self.agg_orc.map_final_scores(final_scores)

        # STEP 4: BUILD FINAL REPORT
        generate_time = datetime.now(timezone.utc)
        return AdvisorReportSchema(
            final_decision=FinalRecommendation(final_score=final_scores[SemanticType.DECISION_SIGNAL], purpose=SemanticType.DECISION_SIGNAL.name,
                                               final_recommend=mapped_labels[SemanticType.DECISION_SIGNAL][1], triggered_rules=triggered_d,
                                               label=mapped_labels[SemanticType.DECISION_SIGNAL][0]),
            final_risk=FinalRecommendation(final_score=final_scores[SemanticType.RISK_LEVEL], 
                                           purpose=SemanticType.RISK_LEVEL.name,
                                           final_recommend=mapped_labels[SemanticType.RISK_LEVEL][1], triggered_rules=triggered_r,
                                           label=mapped_labels[SemanticType.RISK_LEVEL][0]),
            final_opportunity=FinalRecommendation(final_score=final_scores[SemanticType.OPPORTUNITY_RATING], 
                                                  purpose=SemanticType.OPPORTUNITY_RATING.name,
                                                  final_recommend=mapped_labels[SemanticType.OPPORTUNITY_RATING][1], triggered_rules=triggered_o,
                                                  label=mapped_labels[SemanticType.OPPORTUNITY_RATING][0]),
            aggregated_scores=agg_scores,
            ticker=analysis_report.ticker,
            generated_at_utc=generate_time.isoformat(),
            generated_timestamp=int(generate_time.timestamp())
        )
        
    async def get_full_explaination_report(self, analysis_report: QuickCheckAnalysisReport, 
                                 decision_results: Tuple[List[float], List[TriggeredRuleInfo]],
                                 risk_results: Tuple[List[float], List[TriggeredRuleInfo]],
                                 opportunity_results: Tuple[List[float], List[TriggeredRuleInfo]],
                                 meta_weights: Dict[str, float]) -> str:
        """Generate full natural language explanation for advisor recommendations.
        
        Args:
            analysis_report (QuickCheckAnalysisReport): Analysis report to base advice on
            decision_results (Tuple[List[float], List[TriggeredRuleInfo]]): Decision rule results
            risk_results (Tuple[List[float], List[TriggeredRuleInfo]]): Risk rule results
            opportunity_results (Tuple[List[float], List[TriggeredRuleInfo]]): Opportunity rule results
            meta_weights (Dict[str, float]): Meta-rule weights for final synthesis
            
        Returns:
            str: Natural language explanation of the advisor recommendations
        """
        # This function is still correct, it sequences logically
        advisor_report = await self.get_advisor_report(analysis_report, 
                                                       decision_results,
                                                       risk_results,
                                                       opportunity_results,
                                                       meta_weights)
        explanation = self.explainer.explain_report(advisor_report)
        return explanation