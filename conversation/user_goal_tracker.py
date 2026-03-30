# -*- coding: utf-8 -*-
"""
user_goal_tracker.py — Long-term Intent Identifier
Extracts the user's primary macro-goal across a session.
"""

from core.runtime_state import RuntimeState

class UserGoalTracker:
    def __init__(self):
        pass

    def evaluate_goal(self, state: RuntimeState) -> RuntimeState:
        """
        Tracks the overarching user objective (e.g., 'Writing a novel', 'Debugging server').
        """
        text = state.raw_user_input.lower()
        
        # Safe heuristic placeholder
        # TODO: Hook to LLM to parse objective changes
        
        if "help me build" in text or "create" in text:
            state.dialogue_state.primary_goal = "Creation/Building"
        elif "fix this" in text or "error" in text:
            state.dialogue_state.primary_goal = "Troubleshooting"
            
        if state.dialogue_state.primary_goal:
            state.current_goal = state.dialogue_state.primary_goal
            
        return state
