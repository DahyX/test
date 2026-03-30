# -*- coding: utf-8 -*-
"""
style_adapter.py — Tone Tuning
Adapts the output response voice to match user preferences and requested tone.
"""

from core.runtime_state import RuntimeState

class StyleAdapter:
    def __init__(self):
        pass

    def evaluate(self, state: RuntimeState) -> str:
        """Determines syntactic style notes for the final prompt output generator."""
        d_state = state.dialogue_state
        
        if "professional" in d_state.emotional_tone_hint:
            return "formal, professional, objective"
        if "concise" in d_state.detail_preference:
            return "brief, extremely concise, no fluff"
            
        # Default
        return "natural, direct, helpful"
