# -*- coding: utf-8 -*-
"""
context_builder.py — Gathers context from MemoryRouter and appends it to RuntimeState.
"""

from core.runtime_state import RuntimeState
from memory.memory_router import MemoryRouter

class ContextBuilder:
    def __init__(self, memory_router: MemoryRouter):
        self.memory = memory_router
        
    def build(self, state: RuntimeState) -> RuntimeState:
        """
        Populate the RuntimeState's MemoryContext with relevant data.
        """
        # Fetch dynamic context based on Intent/Goal
        query = state.goal if state.goal else state.user_input
        
        # Pull from semantic, episodic, procedural
        context_dict = self.memory.query_context(query)
        
        state.memory_context.semantic = context_dict.get("semantic", "")
        state.memory_context.episodic = context_dict.get("episodic", "")
        state.memory_context.procedural = context_dict.get("procedural", "")
        
        # Working memory is global to the session
        state.memory_context.working = self.memory.working.build_context_string()
        
        return state
