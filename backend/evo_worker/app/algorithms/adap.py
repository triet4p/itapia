"""Adaptive scoring manager for evolutionary algorithms."""

import random
from typing import Any, Dict, Hashable
from app.state import SingletonNameable, Stateful
import app.core.config as cfg


class AdaptiveScoreManager(Stateful):
    """Manages adaptive scoring for evolutionary algorithm components.
    
    Tracks performance of different operators and adapts their usage probabilities
    based on their effectiveness using a learning rate approach.
    """
    
    def __init__(self, lr: float):
        """Initialize the adaptive score manager.
        
        Args:
            lr (float): Learning rate for score adaptation (0.0 to 1.0)
        """
        self._score_storage: Dict[str, float] = {}
        self._score_temp_storage: Dict[str, float] = {}
        self._random = random.Random(cfg.RANDOM_SEED)
        self.lr = lr
        
    def normalize_storage(self) -> None:
        """Normalize stored scores to sum to 1.0."""
        scores = [s for k, s in self._score_storage.items()]
        total_scores = max(1, sum(scores))
        for k in self._score_storage.keys():
            self._score_storage[k] /= total_scores
            
    def normalize_temp_storage(self) -> None:
        """Normalize temporary scores to sum to 1.0."""
        scores = [s for k, s in self._score_temp_storage.items()]
        total_scores = max(1, sum(scores))
        for k in self._score_temp_storage.keys():
            self._score_temp_storage[k] /= total_scores
    
    def init_score(self, obj: SingletonNameable, score: float) -> None:
        """Initialize score for an object.
        
        Args:
            obj (SingletonNameable): Object to initialize score for
            score (float): Initial score value
        """
        self._score_storage[obj.singleton_name] = score
        self._score_temp_storage[obj.singleton_name] = 0.0
        
    def add_temp_score(self, obj: SingletonNameable, additional_score: float) -> None:
        """Add temporary score to an object.
        
        Args:
            obj (SingletonNameable): Object to add score to
            additional_score (float): Additional score to add
        """
        self._score_temp_storage[obj.singleton_name] += additional_score
        
    def update_score(self) -> None:
        """Update scores using learning rate and temporary scores."""
        self.normalize_storage()
        self.normalize_temp_storage()
        for k in self._score_storage.keys():
            new_score = self._score_temp_storage.get(k, 0.0)
            old_score = self._score_storage[k]
            self._score_storage[k] = (1 - self.lr) * old_score + self.lr * new_score
            self._score_temp_storage[k] = 0.0
        
    def select(self) -> str:
        """Select an object based on current scores (roulette wheel selection).
        
        Returns:
            str: Selected object's singleton name
        """
        self.normalize_storage()
        keys = []
        weights = []
        for k, s in self._score_storage.items():
            weights.append(s)
            keys.append(k)
        
        return self._random.choices(keys, weights=weights)[0]
    
    @property
    def fallback_state(self) -> Dict[str, Any]:
        return {
            'random_state': self._random.getstate(),
            'storage': self._score_storage,
            'temp_storage': self._score_temp_storage
        }
        
    def set_from_fallback_state(self, fallback_state: Dict[str, Any]) -> None:
        self._random.setstate(fallback_state['random_state'])
        self._score_storage.clear()
        self._score_storage.update(fallback_state['storage'])
        self._score_temp_storage.clear()
        self._score_temp_storage.update(fallback_state['temp_storage'])
    