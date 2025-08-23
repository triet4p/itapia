# ai_service_quick/app/advisor/orchestrator.py
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
    """
    Phó CEO chuyên trách việc Đưa ra Lời khuyên.
    Điều phối các "Trưởng phòng" để tạo ra một báo cáo tư vấn hoàn chỉnh.
    """
    def __init__(
        self, 
        agg_orc: AggregationOrchestrator,
        explainer: AdvisorExplainerOrchestrator
    ):
        self.agg_orc = agg_orc
        self.explainer = explainer
        logger.info("Advisor Orchestrator initialized with its department heads.")

    async def get_advisor_report(self, analysis_report: QuickCheckAnalysisReport, 
                                 decision_results: Tuple[List[float], List[TriggeredRuleInfo]],
                                 risk_results: Tuple[List[float], List[TriggeredRuleInfo]],
                                 opportunity_results: Tuple[List[float], List[TriggeredRuleInfo]],
                                 meta_weights: Dict[str, float]) -> AdvisorReportSchema:
        logger.info(f"Advisor -> Generating advice for {analysis_report.ticker}...")
        
        # Giải nén kết quả
        (decision_scores, triggered_d) = decision_results
        (risk_scores, triggered_r) = risk_results
        (opportunity_scores, triggered_o) = opportunity_results

        # BƯỚC 3: TỔNG HỢP (Đồng bộ)
        agg_scores = self.agg_orc.aggregate_raw_scores(decision_scores, risk_scores, opportunity_scores)
        final_scores = self.agg_orc.synthesize_final_decision(agg_scores, meta_weights)
        mapped_labels = self.agg_orc.map_final_scores(final_scores)

        # BƯỚC 4: XÂY DỰNG BÁO CÁO CUỐI CÙNG
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
        # Hàm này vẫn đúng, nó tuần tự một cách hợp lý
        advisor_report = await self.get_advisor_report(analysis_report, 
                                                       decision_results,
                                                       risk_results,
                                                       opportunity_results,
                                                       meta_weights)
        explanation = self.explainer.explain_report(advisor_report)
        return explanation