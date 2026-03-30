# -*- coding: utf-8 -*-
"""
lesson_extractor.py — Subconscious Learning
Analyzes the Reflection layer output to generate actionable behavioral Lessons.
"""

from core.runtime_state import RuntimeState
from core.contracts import Lesson

class LessonExtractor:
    def __init__(self):
        pass

    def extract(self, state: RuntimeState) -> RuntimeState:
        """Translates final execution reflections into structured Lessons."""
        if not state.reflection_result:
            return state
            
        evaluation = state.reflection_result.evaluation.lower()
        
        # Heuristic rules
        if "too wordy" in evaluation or "too long" in evaluation:
            lesson = Lesson(
                lesson_type="behavioral",
                trigger="User interrupts or complains about length.",
                recommendation="Decrease verbosity globally."
            )
            state.pending_lessons.append(lesson)
            
        return state
