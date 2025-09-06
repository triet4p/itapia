"""Advisor explainer orchestrator for generating natural language summaries of advisor results."""

from typing import List

# Import required schemas and classes
from itapia_common.schemas.entities.advisor import AdvisorReportSchema, FinalRecommendation, TriggeredRuleInfo


class _FinalRecommendationExplainer:
    """Low-level explainer, explains a single FinalRecommendation block."""
    
    # <<< CHANGE: Remove old templates, keep only what's needed
    _TEMPLATE = "The final {purpose_text} score is {final_score:.2f}, leading to a recommendation of '{recommend_label}'."
    _EVIDENCE_TEMPLATE = " This was primarily driven by signals from: {top_rules_str}."

    def _get_purpose_text(self, purpose: str) -> str:
        """Get human-readable purpose text from purpose code.
        
        Args:
            purpose (str): Purpose code string
            
        Returns:
            str: Human-readable purpose description
        """
        if "DECISION" in purpose: 
            return "decision"
        if "RISK" in purpose: 
            return "risk"
        if "OPPORTUNITY" in purpose: 
            return "opportunity"
        return "overall"

    def _format_top_rules_str(self, rules: List[TriggeredRuleInfo]) -> str:
        """Get names of up to 3 most influential rules.
        
        Args:
            rules (List[TriggeredRuleInfo]): List of triggered rules
            
        Returns:
            str: Formatted string of top rule names
        """
        if not rules:
            return "no specific signals"
        # Sort rules by absolute score value
        sorted_rules = sorted(rules, key=lambda r: abs(r.score), reverse=True)
        # Get names of top 3 rules
        rule_names = [f"'{r.name}'" for r in sorted_rules[:3]]
        return ", ".join(rule_names)

    def explain(self, report: FinalRecommendation) -> str:
        """Generate natural language explanation for a FinalRecommendation.
        
        Args:
            report (FinalRecommendation): Final recommendation to explain
            
        Returns:
            str: Natural language explanation
        """
        if not report.triggered_rules:
            purpose_text = self._get_purpose_text(report.purpose)  # Try to guess purpose
            return f"No specific signals were triggered for the {purpose_text} assessment, resulting in a neutral stance."

        # Get purpose from first rule (all have the same purpose)
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
    """Generates natural language summaries for Advisor results.
    
    Provides both aggregated explanations and individual rule explanations.
    """
    
    _HEADER_TEMPLATE = "Advisor Recommendation for {ticker}:"
    _MAIN_RECOMMENDATION_TEMPLATE = "=> Main Recommendation: {decision_recommendation}"
    _CONTEXT_TEMPLATE = """
Analysis Context:
- {risk_recommendation}
- {opportunity_recommendation}
"""

    def __init__(self):
        """Initialize the advisor explainer orchestrator."""
        # <<< CHANGE: Receive dependency injection
        self.rec_explainer = _FinalRecommendationExplainer()

    def explain_report(self, report: AdvisorReportSchema) -> str:
        """Generate a comprehensive natural language explanation for an AdvisorReport.
        
        Args:
            report (AdvisorReportSchema): Advisor report to explain
            
        Returns:
            str: Comprehensive natural language explanation
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
