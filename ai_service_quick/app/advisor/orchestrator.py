# ai_service_quick/app/advisor/orchestrator.py
import math
from typing import List

from itapia_common.rules.rule import Rule
from itapia_common.schemas.enums import SemanticType
from itapia_common.dblib.services.rules import RuleService
from itapia_common.rules.score import ScoreAggregator, ScoreFinalMapper
from itapia_common.rules import builtin
from itapia_common.schemas.entities.advisor import AdvisorReportSchema, TriggeredRuleInfo, AggregatedScoreInfo, FinalRecommendation
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from itapia_common.logger import ITAPIALogger
# Giả định có một lớp UserProfile và MetaRule trong tương lai
# from itapia_common.models import UserProfile 
# from itapia_common.rules.meta_rule import MetaRule

logger = ITAPIALogger('Advisor Orchestrator')

class AdvisorOrchestrator:
    """
    Điều phối viên cho module Advisor.
    Nhận một báo cáo phân tích đầy đủ và đưa ra các khuyến nghị cuối cùng
    bằng cách thực thi các bộ quy tắc.
    """
    def __init__(self, rule_service: RuleService):
        self.rule_service = rule_service
        self.aggregator = ScoreAggregator()
        self.mapper = ScoreFinalMapper()
        logger.info("Advisor Orchestrator initialized.")

    async def get_advisor_report(self, report: QuickCheckAnalysisReport) -> AdvisorReportSchema:
        """
        Quy trình chính để tạo ra một báo cáo tư vấn hoàn chỉnh.
        """
        logger.info(f"Advisor -> Generating advice for {report.ticker}...")
        
        # <<< THAY ĐỔI: Tạo các danh sách riêng để thu thập bằng chứng cho mỗi purpose
        triggered_decision_rules: List[TriggeredRuleInfo] = []
        triggered_risk_rules: List[TriggeredRuleInfo] = []
        triggered_opportunity_rules: List[TriggeredRuleInfo] = []

        # === TẦNG 1: CHẠY CÁC BỘ QUY TẮC ĐỘC LẬP VÀ THU THẬP BẰNG CHỨNG RIÊNG ===
        decision_scores = self._run_rules_and_collect(report, SemanticType.DECISION_SIGNAL, triggered_decision_rules)
        risk_scores = self._run_rules_and_collect(report, SemanticType.RISK_LEVEL, triggered_risk_rules)
        opportunity_scores = self._run_rules_and_collect(report, SemanticType.OPPORTUNITY_RATING, triggered_opportunity_rules)

        # === TẦNG 2: TỔNG HỢP KẾT QUẢ THÔ ===
        agg_decision = self.aggregator.average(decision_scores)
        agg_risk = self.aggregator.get_highest_score(risk_scores)
        agg_opportunity = self.aggregator.get_highest_score(opportunity_scores)
        
        aggregated_scores = AggregatedScoreInfo(
            raw_decision_score=agg_decision,
            raw_risk_score=agg_risk,
            raw_opportunity_score=agg_opportunity
        )

        # === TẦNG 3: META-SYNTHESIS (HIỆN TẠI DÙNG LOGIC ĐƠN GIẢN) ===
        # Placeholder cho logic cá nhân hóa và MetaRule
        final_decision_score = agg_decision # Sẽ được thay thế bằng MetaRule_D sau
        final_risk_score = agg_risk         # Sẽ được thay thế bằng MetaRule_R sau
        final_opportunity_score = agg_opportunity # Sẽ được thay thế bằng MetaRule_O sau

        # === TẦNG 4: MAPPING SANG NHÃN CUỐI CÙNG ===
        decision_desc = self.mapper.map(final_decision_score, SemanticType.DECISION_SIGNAL)
        risk_desc = self.mapper.map(final_risk_score, SemanticType.RISK_LEVEL)
        opportunity_desc = self.mapper.map(final_opportunity_score, SemanticType.OPPORTUNITY_RATING)

        # === TẦNG 5: TẠO BÁO CÁO HOÀN CHỈNH THEO SCHEMA MỚI ===
        advisor_report = AdvisorReportSchema(
            # Xây dựng từng đối tượng FinalRecommendation với bằng chứng tương ứng
            final_decision=FinalRecommendation(
                final_score=final_decision_score, 
                final_recommend=decision_desc,
                triggered_rules=triggered_decision_rules
            ),
            final_risk=FinalRecommendation(
                final_score=final_risk_score,
                final_recommend=risk_desc,
                triggered_rules=triggered_risk_rules
            ),
            final_opportunity=FinalRecommendation(
                final_score=final_opportunity_score,
                final_recommend=opportunity_desc,
                triggered_rules=triggered_opportunity_rules
            ),
            
            aggregated_scores=aggregated_scores,
            ticker=report.ticker,
            generated_at_utc=report.generated_at_utc,
            generated_timestamp=report.generated_timestamp
        )
        
        logger.info(f"Advisor -> Advice for {report.ticker} generated successfully.")
        return advisor_report

    def _run_rules_and_collect(self, report: QuickCheckAnalysisReport, purpose: SemanticType, collection: List[TriggeredRuleInfo]) -> List[float]:
        """
        Chạy các quy tắc cho một mục đích cụ thể và điền vào danh sách `collection` được cung cấp.
        """
        # <<< THAY ĐỔI: Sử dụng RuleService để lấy quy tắc từ CSDL
        # Giả sử RuleService có phương thức `get_active_rules_by_purpose` trả về List[Rule]
        # Trong thực tế, bạn có thể cần một lớp trung gian để chuyển từ RuleSchema sang Rule
        # Hoặc RuleService có thể trả về trực tiếp đối tượng Rule.
        rules_entity = self.rule_service.get_active_rules_by_purpose(purpose)
        
        rules = [Rule.from_dict(re.model_dump()) for re in rules_entity]
        
        scores = []
        for rule in rules:
            score = rule.execute(report)
            scores.append(score)
            # Chỉ thêm vào bằng chứng nếu quy tắc có tín hiệu khác trung lập
            if not math.isclose(score, 0.0):
                 collection.append(TriggeredRuleInfo(
                     rule_id=rule.rule_id, 
                     name=rule.name, 
                     score=score, 
                     purpose=purpose.name
                 ))
        return scores