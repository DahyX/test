# -*- coding: utf-8 -*-
"""
structure_selector.py — Output Framing
Determines the structural markdown format of the response (e.g., bullets vs step-by-step vs paragraph).
"""

from core.runtime_state import RuntimeState

class StructureSelector:
    def __init__(self):
        pass

    def evaluate(self, state: RuntimeState) -> str:
        """Heuristic selector for output shapes."""
        mode = state.inferred_mode
        
        if mode == "coding" or mode == "debugging":
            return "code_blocks_with_explanations"
        elif mode == "factual_qa":
            return "direct_answer_with_sources"
        elif mode == "planning":
            return "step_by_step_list"
        else:
            return "conversational_paragraphs"
