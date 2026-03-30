# -*- coding: utf-8 -*-
"""
tool_policy.py — Tool Pre-Flight Safety
Heuristic rules defining whether external actions are permitted based on the current state's uncertainty profile.
"""

from core.runtime_state import RuntimeState

class ToolPolicy:
    def __init__(self):
        self.forbidden_modes = ["chat", "tutoring"]

    def is_permitted(self, state: RuntimeState) -> bool:
        """Validates if triggering external tool execution is safe and logically necessary."""
        # 1. Mode blocking
        if state.inferred_mode in self.forbidden_modes:
            return False
            
        # 2. Risk blocking (Avoid if uncertainty is extremely high to prevent cascading failures)
        if state.uncertainty_profile.ambiguity_score > 0.8:
            return False
            
        # 3. Policy overrides
        if state.reasoning_policy.use_tools:
            return True
            
        return False
