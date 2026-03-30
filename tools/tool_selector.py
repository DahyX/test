# -*- coding: utf-8 -*-
"""
tool_selector.py — Action Resolution
Selects the optimal tool and parameters given a validated tool usage permission.
"""

from core.runtime_state import RuntimeState
from tools.tool_policy import ToolPolicy
from core.contracts import ToolDecision

class ToolSelector:
    def __init__(self):
        self.policy = ToolPolicy()

    def select(self, state: RuntimeState) -> RuntimeState:
        """Populates the ToolDecision sub-state."""
        decision = ToolDecision()
        
        # Check permissions
        decision.should_use_tools = self.policy.is_permitted(state)
        if not decision.should_use_tools:
            decision.rationale = "Tool use blocked by policy or ambiguity."
            state.tool_decision = decision
            return state
            
        # TODO: Hook LLM here or tool embeddings to pick best tool
        # Fake heuristic placeholder
        text = state.raw_user_input.lower()
        if "search" in text or "look up" in text:
            decision.selected_tools.append("web_search")
            
        if "read file" in text:
            decision.selected_tools.append("read_file")
            
        state.tool_decision = decision
        return state
