# -*- coding: utf-8 -*-
"""
uncertainty_estimator.py — Confidence Scoring
Calculates fractional confidence metrics for user intent, factual bounds, and plan viability.
"""

from core.runtime_state import RuntimeState
from core.contracts import UncertaintyProfile

class UncertaintyEstimator:
    """Estimates ambiguity and factual danger."""
    
    def __init__(self):
        pass

    def evaluate(self, state: RuntimeState) -> UncertaintyProfile:
        """
        Calculates confidence flags. 
        TODO: Replace length heuristic with LLM perplexity checks.
        """
        profile = UncertaintyProfile()
        text = state.raw_user_input.lower()
        
        # Ambiguity heuristic: short questions with low context
        if len(text.split()) < 4 and "?" in text:
            profile.ambiguity_score = 0.8
            profile.requires_verification = True
            profile.assumptions.append("User might be referring to recent context.")
            
        # Danger heuristic
        danger_words = ["rm -rf", "delete", "format", "drop table"]
        if any(w in text for w in danger_words):
            profile.plan_confidence = 0.1
            profile.requires_verification = True
            
        # Ensure normalization
        profile.overall_confidence = (profile.factual_confidence + profile.plan_confidence) / 2.0
        
        return profile
