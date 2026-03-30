# -*- coding: utf-8 -*-
"""
dialogue_state.py — Graph/Thread State Tracker
Maintains the macroscopic state of the conversation.
"""

import os
from core.contracts import DialogueState
from core.runtime_state import RuntimeState

class DialogueManager:
    """Updates the DialogueState Pydantic model by evaluating conversation trajectories."""
    def __init__(self):
        pass

    def update(self, state: RuntimeState) -> RuntimeState:
        """
        Extracts preferences and conversational stages into the state.
        """
        # Load from state
        d_state = state.dialogue_state
        
        # Heuristic Goal extraction
        text = state.raw_user_input.lower()
        
        if "be short" in text or "brief" in text:
            d_state.detail_preference = "concise"
            d_state.preference_hints.append("User requested brevity.")
            
        if "explain" in text or "how does" in text:
            d_state.detail_preference = "verbose"
            d_state.current_stage = "informing"
            
        # Maintain state
        state.dialogue_state = d_state
        return state
