# -*- coding: utf-8 -*-
"""
mode_selector.py — Intent and Mode Classification
Identifies what cognitive mode Jarvis should enter (e.g. coding, tutor, chat).
"""

from core.runtime_state import RuntimeState
import re

class ModeSelector:
    """Classifies user interaction intent."""
    
    def __init__(self):
        # TODO: Wire to LLM embedding classifier
        self.code_heuristics = ["python", "code", "debug", "script", "function", "error"]
        self.planning_heuristics = ["plan", "schedule", "remind", "workflow"]

    def detect(self, state: RuntimeState) -> str:
        """Heuristic placeholder logic to detect mode."""
        text = state.raw_user_input.lower()
        
        # Safe heuristic placeholder
        has_code = any(word in text for word in self.code_heuristics)
        has_plan = any(word in text for word in self.planning_heuristics)
        
        if has_code and ("fix" in text or "error" in text):
            return "debugging"
        elif has_code:
            return "coding"
        elif has_plan:
            return "planning"
        elif "?" in text:
            return "factual_qa"
            
        return "chat"
