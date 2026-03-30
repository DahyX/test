# -*- coding: utf-8 -*-
"""
behavior_updater.py — Lesson Promotion
Decides whether a pending Lesson should be promoted to active Procedural memory or ignored.
"""

from core.runtime_state import RuntimeState

class BehaviorUpdater:
    def __init__(self):
        self.promotion_threshold = 0.8

    def evaluate(self, state: RuntimeState) -> RuntimeState:
        """Filters lessons and flags them for promotion."""
        if not state.pending_lessons:
            return state
            
        valid_lessons = []
        for lesson in state.pending_lessons:
            if lesson.confidence >= self.promotion_threshold:
                lesson.promote_to_procedural = True
                valid_lessons.append(lesson)
                
        state.pending_lessons = valid_lessons
        return state
