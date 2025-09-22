"""Personal analysis orchestrator for user profile and customization management."""

from typing import List

from itapia_common.logger import ITAPIALogger
from itapia_common.schemas.entities.personal import QuantitivePreferencesConfig
from itapia_common.schemas.entities.profiles import ProfileEntity
from itapia_common.schemas.entities.rules import RuleEntity

from .preferences import PreferencesManager
from .quantitive import QuantitivePreferencesAnalyzer
from .scorer import Scorer

logger = ITAPIALogger("Personal Analysis Orchestrator")


class PersonalAnalysisOrchestrator:
    """Deputy CEO responsible for Personalization.

    Provides configurations (weights, selectors) based on user profiles.
    """

    def __init__(
        self,
        quantitive_analyzer: QuantitivePreferencesAnalyzer,
        preferences_manager: PreferencesManager,
        scorer: Scorer,
    ):
        """Initialize the personal analysis orchestrator in MVP placeholder mode.

        Args:
            quantitive_analyzer (QuantitivePreferencesAnalyzer): Analyzer for quantitative preferences
            preferences_manager (PreferencesManager): Manager for user preferences
            scorer (Scorer): Scorer for evaluating rules
        """
        self._default_meta_weights = {
            "decision": 1.0,
            "risk": 0.15,
            "opportunity": 0.05,
        }
        self.quantitive_analyzer = quantitive_analyzer
        self.preferences_manager = preferences_manager
        self.scorer = scorer
        logger.info(
            "Personal Analysis Orchestrator initialized (MVP placeholder mode)."
        )

    def get_suggest_config(self, profile: ProfileEntity) -> QuantitivePreferencesConfig:
        """Get suggested quantitative preferences configuration based on user profile.

        Args:
            profile (ProfileEntity): User investment profile

        Returns:
            QuantitivePreferencesConfig: Suggested quantitative preferences configuration
        """
        return self.quantitive_analyzer.get_suggested_config(profile)

    def filter_rules(
        self,
        rules: List[RuleEntity],
        quantitive_config: QuantitivePreferencesConfig,
        limit: int = 10,
    ):
        """Filter and rank rules based on quantitative preferences.

        Args:
            rules (List[RuleEntity]): List of rules to filter
            quantitive_config (QuantitivePreferencesConfig): Quantitative preferences configuration
            limit (int): Maximum number of rules to return

        Returns:
            Filtered and ranked list of rules
        """
        return self.preferences_manager.filter_rules(
            rules, scorer=self.scorer, quantitive_config=quantitive_config, limit=limit
        )
