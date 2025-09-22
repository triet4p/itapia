"""Advisor orchestrator for coordinating advice generation processes."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

import numpy as np
from itapia_common.logger import ITAPIALogger
from itapia_common.rules.action import _BaseActionMapper
from itapia_common.schemas.entities.action import Action
from itapia_common.schemas.entities.advisor import (
    AdvisorReportSchema,
    AggregatedScoreInfo,
    FinalRecommendation,
    TriggeredRuleInfo,
)
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from itapia_common.schemas.entities.personal import BehaviorModifiers
from itapia_common.schemas.entities.rules import SemanticType

from .aggeration import AggregationOrchestrator
from .explainer import AdvisorExplainerOrchestrator

logger = ITAPIALogger("Advisor Orchestrator")


class AdvisorOrchestrator:
    """Deputy CEO responsible for Providing Advice.

    Orchestrates department heads to create a complete advisory report.
    """

    def __init__(
        self,
        agg_orc: AggregationOrchestrator,
        explainer: AdvisorExplainerOrchestrator,
        default_action_mapper: _BaseActionMapper,
    ):
        """Initialize the advisor orchestrator with required components.

        Args:
            agg_orc (AggregationOrchestrator): Aggregation orchestrator instance
            explainer (AdvisorExplainerOrchestrator): Advisor explainer instance
            default_action_mapper (_BaseActionMapper): An action mapper to map final score to an action
        """
        self.agg_orc = agg_orc
        self.explainer = explainer
        self.default_action_mapper = default_action_mapper
        logger.info("Advisor Orchestrator initialized with its department heads.")

    async def get_advisor_report(
        self,
        analysis_report: QuickCheckAnalysisReport,
        decision_results: Tuple[List[float], List[TriggeredRuleInfo]],
        risk_results: Tuple[List[float], List[TriggeredRuleInfo]],
        opportunity_results: Tuple[List[float], List[TriggeredRuleInfo]],
        behavior_modifiers: Optional[BehaviorModifiers] = None,
        action_mapper: Optional[_BaseActionMapper] = None,
    ) -> AdvisorReportSchema:
        """Generate advisor report based on analysis results and rule evaluations.

        Args:
            analysis_report (QuickCheckAnalysisReport): Analysis report to base advice on
            decision_results (Tuple[List[float], List[TriggeredRuleInfo]]): Decision rule results
            risk_results (Tuple[List[float], List[TriggeredRuleInfo]]): Risk rule results
            opportunity_results (Tuple[List[float], List[TriggeredRuleInfo]]): Opportunity rule results
            behavior_modifiers (Optional[BehaviorModifiers]): Used to modify final results based on specific user demands
            action_mapper (Optional[_BaseActionMapper]): An action mapper to map final score to an action

        Returns:
            AdvisorReportSchema: Complete advisor report
        """
        logger.info(f"Advisor -> Generating advice for {analysis_report.ticker}...")

        # Choose action mapper
        action_mapper = action_mapper if action_mapper else self.default_action_mapper

        # Unpack results
        (decision_scores, triggered_d) = decision_results
        (risk_scores, triggered_r) = risk_results
        (opportunity_scores, triggered_o) = opportunity_results

        # STEP 3: AGGREGATION (Synchronous)
        agg_scores = self.agg_orc.aggregate_raw_scores(
            decision_scores, risk_scores, opportunity_scores
        )

        base_action = action_mapper.map_action(agg_scores.raw_decision_score)
        gated_action = self._apply_gating_logic(base_action, agg_scores)
        final_action = self._apply_behavior_modifiers(gated_action, behavior_modifiers)

        # --- STEP 3: CREATE FINAL LABELS AND RECOMMENDATIONS ---
        # Use AggregationOrchestrator mapper to get labels for raw scores
        decision_label, decision_recommend = self.agg_orc.mapper.map(
            agg_scores.raw_decision_score, SemanticType.DECISION_SIGNAL
        )
        risk_label, risk_recommend = self.agg_orc.mapper.map(
            agg_scores.raw_risk_score, SemanticType.RISK_LEVEL
        )
        opportunity_label, opportunity_recommend = self.agg_orc.mapper.map(
            agg_scores.raw_opportunity_score, SemanticType.OPPORTUNITY_RATING
        )

        # Create a final recommendation based on final_action
        # This is the final interpretation for the user
        final_decision_recommendation = self._create_final_recommendation_text(
            final_action, triggered_d
        )

        # --- STEP 4: BUILD COMPLETE REPORT ---
        generate_time = datetime.now(timezone.utc)
        return AdvisorReportSchema(
            final_decision=FinalRecommendation(
                final_score=agg_scores.raw_decision_score,
                purpose=SemanticType.DECISION_SIGNAL.name,
                final_recommend=final_decision_recommendation,
                triggered_rules=triggered_d,
                label=decision_label,
            ),
            final_risk=FinalRecommendation(
                final_score=agg_scores.raw_risk_score,
                purpose=SemanticType.RISK_LEVEL.name,
                final_recommend=risk_recommend,
                triggered_rules=triggered_r,
                label=risk_label,
            ),
            final_opportunity=FinalRecommendation(
                final_score=agg_scores.raw_opportunity_score,
                purpose=SemanticType.OPPORTUNITY_RATING.name,
                final_recommend=opportunity_recommend,
                triggered_rules=triggered_o,
                label=opportunity_label,
            ),
            aggregated_scores=agg_scores,
            # (Important) Add final_action to schema so Frontend can use it
            final_action=final_action,
            ticker=analysis_report.ticker,
            generated_at_utc=generate_time.isoformat(),
            generated_timestamp=int(generate_time.timestamp()),
        )

    def _apply_gating_logic(
        self, base_action: Action, agg_scores: AggregatedScoreInfo
    ) -> Action:
        """Apply simple if-else logic to adjust the base action.

        Args:
            base_action (Action): Base action to adjust
            agg_scores (AggregatedScoreInfo): Aggregated scores for decision making

        Returns:
            Action: Adjusted action based on gating logic
        """
        action = base_action

        # RISK GATE: Highest priority
        # Assume RISK_THRESHOLDS: VERY_HIGH > 0.9, HIGH > 0.8
        if agg_scores.raw_risk_score >= 0.9:  # Very high risk
            if action.action_type == "BUY":
                logger.info(
                    "RISK GATE: Very High risk detected. Overriding BUY signal to HOLD."
                )
                return Action(action_type="HOLD")
        elif agg_scores.raw_risk_score >= 0.8:  # High risk
            if action.action_type == "BUY":
                logger.info(
                    "RISK GATE: High risk detected. Reducing position size by 50%."
                )
                action_dict = action.model_dump()
                action_dict["position_size_pct"] = action.position_size_pct * 0.5
                action = Action.model_validate(action_dict)

        # OPPORTUNITY GATE: Only apply if no high risk
        # Assume OPPORTUNITY_THRESHOLDS: TOP_TIER > 0.9
        if agg_scores.raw_risk_score < 0.8 and agg_scores.raw_opportunity_score >= 0.9:
            if action.action_type == "BUY":
                logger.info(
                    "OPPORTUNITY GATE: Top-tier opportunity. Increasing position size by 20%."
                )
                new_size = action.position_size_pct * 1.2
                action_dict = action.model_dump()
                action_dict["position_size_pct"] = np.clip(new_size, 0.0, 1.0)
                action = Action.model_validate(action_dict)

        return action

    def _apply_behavior_modifiers(
        self, base_action: Action, modifiers: Optional[BehaviorModifiers]
    ) -> Action:
        """Apply personalized user behavior adjustment parameters.

        Args:
            base_action (Action): Base action to adjust
            modifiers (Optional[BehaviorModifiers]): User behavior modifiers

        Returns:
            Action: Action adjusted with user behavior modifiers
        """
        if not modifiers or base_action.action_type == "HOLD":
            return base_action

        new_size = base_action.position_size_pct * modifiers.position_sizing_factor
        new_sl = base_action.sl_pct * modifiers.risk_tolerance_factor
        new_tp = base_action.tp_pct * modifiers.risk_tolerance_factor

        final_size = np.clip(new_size, 0.0, 1.0)
        final_sl = np.clip(new_sl, 0.01, 0.5)
        final_tp = np.clip(new_tp, 0.02, 1.0)

        return Action(
            position_size_pct=round(final_size, 3),
            sl_pct=round(final_sl, 3),
            tp_pct=round(final_tp, 3),
            action_type=base_action.action_type,
            duration_days=base_action.duration_days,
        )

    def _create_final_recommendation_text(
        self, final_action: Action, triggered_rules: List[TriggeredRuleInfo]
    ) -> str:
        """Create final recommendation text for the user.

        Args:
            final_action (Action): Final action to create text for
            triggered_rules (List[TriggeredRuleInfo]): List of triggered rules

        Returns:
            str: Natural language recommendation text
        """
        if final_action.action_type == "HOLD":
            return "Recommendation: HOLD. No clear trading signal based on current analysis and risk assessment."

        action_text = "BUY" if final_action.action_type == "BUY" else "SELL"

        return (
            f"Recommendation: {action_text}. "
            f"Suggested Position Size: {final_action.position_size_pct:.0%}. "
            f"Stop-Loss: ~{final_action.sl_pct:.1%}, Take-Profit: ~{final_action.tp_pct:.1%}. "
            f"Triggered by {len(triggered_rules)} rules."
        )

    async def get_full_explaination_report(
        self,
        analysis_report: QuickCheckAnalysisReport,
        decision_results: Tuple[List[float], List[TriggeredRuleInfo]],
        risk_results: Tuple[List[float], List[TriggeredRuleInfo]],
        opportunity_results: Tuple[List[float], List[TriggeredRuleInfo]],
        behavior_modifiers: Optional[BehaviorModifiers] = None,
        action_mapper: Optional[_BaseActionMapper] = None,
    ) -> str:
        """Generate full natural language explanation for advisor recommendations.

        Args:
            analysis_report (QuickCheckAnalysisReport): Analysis report to base advice on
            decision_results (Tuple[List[float], List[TriggeredRuleInfo]]): Decision rule results
            risk_results (Tuple[List[float], List[TriggeredRuleInfo]]): Risk rule results
            opportunity_results (Tuple[List[float], List[TriggeredRuleInfo]]): Opportunity rule results
            behavior_modifiers (Optional[BehaviorModifiers]): Behavior modifiers for personalization
            action_mapper (Optional[_BaseActionMapper]): Action mapper to use

        Returns:
            str: Natural language explanation of the advisor recommendations
        """
        # This function is still correct, it sequences logically
        advisor_report = await self.get_advisor_report(
            analysis_report,
            decision_results,
            risk_results,
            opportunity_results,
            behavior_modifiers,
            action_mapper,
        )
        explanation = self.explainer.explain_report(advisor_report)
        return explanation
