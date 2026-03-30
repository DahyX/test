# -*- coding: utf-8 -*-
"""
controller.py — Master Reasoning Controller
Orchestrates ModeSelection and Uncertainty to emit a final ReasoningPolicy.
"""

from core.runtime_state import RuntimeState
from reasoning.mode_selector import ModeSelector
from reasoning.uncertainty_estimator import UncertaintyEstimator

class ReasoningController:
    """Sets the macro-reasoning policy for the agent loop."""
    
    def __init__(self):
        self.mode = ModeSelector()
        self.uncertainty = UncertaintyEstimator()

    def formulate_policy(self, state: RuntimeState) -> RuntimeState:
        """
        Updates RuntimeState with inferred mode, uncertainty profile, and policy.
        """
        # 1. Detect Mode
        state.inferred_mode = self.mode.detect(state)
        
        # 2. Estimate Uncertainty
        state.uncertainty_profile = self.uncertainty.evaluate(state)
        
        # 3. Formulate Policy
        policy = state.reasoning_policy
        policy.response_mode = state.inferred_mode
        policy.verification_required = state.uncertainty_profile.requires_verification
        
        if state.uncertainty_profile.ambiguity_score > 0.6:
            policy.caution_level = "high"
            policy.answer_style = "clarifying"
            policy.verbosity = 2
        else:
            policy.caution_level = "low"
            # Increase verbosity slightly for tutorial/coding modes
            if policy.response_mode in ["coding", "tutoring"]:
                policy.verbosity = 3
                
        # Heuristic for tool and memory usage
        if policy.response_mode in ["planning", "factual_qa", "debugging"]:
            policy.retrieve_memory = True
            
        return state
