# -*- coding: utf-8 -*-
"""
answer_planner.py — Final Response Strategy
Fuses Structure, Style, and Runtime constraints to build a strict ResponsePlan for the generator.
"""

from core.runtime_state import RuntimeState
from response.structure_selector import StructureSelector
from response.style_adapter import StyleAdapter

class AnswerPlanner:
    def __init__(self):
        self.structure = StructureSelector()
        self.style = StyleAdapter()

    def formulate_plan(self, state: RuntimeState) -> RuntimeState:
        """Updates the state's ResponsePlan with strict generation boundaries."""
        plan = state.response_plan
        
        plan.target_structure = self.structure.evaluate(state)
        plan.style_notes = self.style.evaluate(state)
        
        # Verify if caveats are needed based on Reasoning Uncertainty
        if state.uncertainty_profile.requires_verification or state.uncertainty_profile.factual_confidence < 0.6:
            plan.should_include_caveats = True
            plan.opening_strategy = "Acknowledge uncertainty, then attempt answer."
            
        state.response_plan = plan
        return state
