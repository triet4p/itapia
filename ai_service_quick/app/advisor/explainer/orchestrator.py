# ai_service_quick/app/explainer/advisor/orchestrator.py

from typing import List

# Import các schema và lớp cần thiết
from itapia_common.schemas.entities.advisor import AdvisorReportSchema, FinalRecommendation, TriggeredRuleInfo

class _FinalRecommendationExplainer:
    """Explainer cấp thấp, giải thích một khối FinalRecommendation duy nhất."""
    
    # <<< THAY ĐỔI: Bỏ các template cũ, chỉ giữ lại những gì cần thiết
    _TEMPLATE = "The final {purpose_text} score is {final_score:.2f}, leading to a recommendation of '{recommend_label}'."
    _EVIDENCE_TEMPLATE = " This was primarily driven by signals from: {top_rules_str}."

    def _get_purpose_text(self, purpose: str) -> str:
        if "DECISION" in purpose: return "decision"
        if "RISK" in purpose: return "risk"
        if "OPPORTUNITY" in purpose: return "opportunity"
        return "overall"

    def _format_top_rules_str(self, rules: List[TriggeredRuleInfo]) -> str:
        """Lấy tên của tối đa 3 quy tắc có ảnh hưởng nhất."""
        if not rules:
            return "no specific signals"
        # Sắp xếp các quy tắc theo giá trị tuyệt đối của điểm số
        sorted_rules = sorted(rules, key=lambda r: abs(r.score), reverse=True)
        # Lấy tên của 3 quy tắc hàng đầu
        rule_names = [f"'{r.name}'" for r in sorted_rules[:3]]
        return ", ".join(rule_names)

    def explain(self, report: FinalRecommendation) -> str:
        if not report.triggered_rules:
            purpose_text = self._get_purpose_text(report.purpose) # Cố gắng đoán purpose
            return f"No specific signals were triggered for the {purpose_text} assessment, resulting in a neutral stance."

        # Lấy purpose từ quy tắc đầu tiên (tất cả đều có cùng purpose)
        purpose_text = self._get_purpose_text(report.triggered_rules[0].purpose)
        
        explanation = self._TEMPLATE.format(
            purpose_text=purpose_text,
            final_score=report.final_score,
            recommend_label=report.final_recommend.upper()
        )
        
        top_rules_str = self._format_top_rules_str(report.triggered_rules)
        explanation += self._EVIDENCE_TEMPLATE.format(top_rules_str=top_rules_str)
            
        return explanation

class AdvisorExplainerOrchestrator:
    """
    Tạo ra các bản tóm tắt bằng ngôn ngữ tự nhiên cho kết quả của Advisor.
    Cung cấp cả giải thích tổng hợp và giải thích cho từng quy tắc riêng lẻ.
    """
    _HEADER_TEMPLATE = "Advisor Recommendation for {ticker}:"
    _MAIN_RECOMMENDATION_TEMPLATE = "=> Main Recommendation: {decision_recommendation}"
    _CONTEXT_TEMPLATE = "\nAnalysis Context:\n- {risk_recommendation}\n- {opportunity_recommendation}"

    def __init__(self):
        # <<< THAY ĐỔI: Nhận dependency injection
        self.rec_explainer = _FinalRecommendationExplainer()

    def explain_report(self, report: AdvisorReportSchema) -> str:
        """
        Tạo ra một chuỗi văn bản giải thích TỔNG HỢP cho AdvisorReport.
        """
        if not isinstance(report, AdvisorReportSchema):
            return "Invalid advisor report format provided for explanation."

        decision_explanation = self.rec_explainer.explain(report.final_decision)
        risk_explanation = self.rec_explainer.explain(report.final_risk)
        opportunity_explanation = self.rec_explainer.explain(report.final_opportunity)

        header = self._HEADER_TEMPLATE.format(ticker=report.ticker)
        
        main_recommendation_section = self._MAIN_RECOMMENDATION_TEMPLATE.format(
            decision_recommendation=report.final_decision.final_recommend.upper()
        )
        
        full_decision_explanation = f"Decision Breakdown: {decision_explanation}"
        
        context_section = self._CONTEXT_TEMPLATE.format(
            risk_recommendation=f"Risk Assessment: {risk_explanation}",
            opportunity_recommendation=f"Opportunity Scan: {opportunity_explanation}"
        )

        return "\n\n".join([
            header,
            main_recommendation_section,
            full_decision_explanation,
            context_section
        ])