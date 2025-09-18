"""Personal analysis orchestrator for user profile and customization management."""

from typing import List, Dict, Callable, Any

from itapia_common.rules.rule import Rule
from itapia_common.logger import ITAPIALogger
from itapia_common.schemas.entities.personal import QuantitivePreferencesConfig
from itapia_common.schemas.entities.profiles import ProfileEntity
from itapia_common.schemas.entities.rules import RuleEntity

from .quantitive import QuantitivePreferencesAnalyzer
from .preferences import PreferencesManager
from .scorer import Scorer

logger = ITAPIALogger('Personal Analysis Orchestrator')


class PersonalAnalysisOrchestrator:
    """Deputy CEO responsible for Personalization.
    
    Provides configurations (weights, selectors) based on user profiles.
    """
    
    def __init__(self, quantitive_analyzer: QuantitivePreferencesAnalyzer,
                 preferences_manager: PreferencesManager,
                 scorer: Scorer):
        """Initialize the personal analysis orchestrator in MVP placeholder mode."""
        self._default_meta_weights = {"decision": 1.0, "risk": 0.15, "opportunity": 0.05}
        self.quantitive_analyzer = quantitive_analyzer
        self.preferences_manager = preferences_manager
        self.scorer = scorer
        logger.info("Personal Analysis Orchestrator initialized (MVP placeholder mode).")
        
    def get_suggest_config(self, profile: ProfileEntity) -> QuantitivePreferencesConfig:
        return self.quantitive_analyzer.get_suggested_config(profile)
    
    def filter_rules(self, rules: List[RuleEntity], quantitive_config: QuantitivePreferencesConfig,
                     limit: int = 10):
        return self.preferences_manager.filter_rules(rules, scorer=self.scorer,
                                                     quantitive_config=quantitive_config,
                                                     limit=limit)