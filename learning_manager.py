# -*- coding: utf-8 -*-
"""
learning_manager.py — Jarvis V5 Autonomous Learning Scheduler
Queues missing knowledge topics for the background thread instead of crawling instantly.
"""

import json

class LearningManager:
    def __init__(self, memory, backend_learner):
        self.memory = memory
        self.learner = backend_learner

    def add_to_backlog(self, topic: str, priority: int = 1):
        """Add a topic to the learning backlog if not already there."""
        if not topic:
            return
            
        topics = self._get_backlog()
        existing = [t for t in topics if t["topic"].lower() == topic.lower()]
        if not existing:
            topics.append({"topic": topic, "priority": priority})
            self._save_backlog(topics)
            self._push_top_to_learner()

    def _get_backlog(self) -> list:
        entry = self.memory.get_working("learning_backlog_v5")
        if entry:
            return json.loads(entry["value"])
        return []

    def _save_backlog(self, topics: list):
        self.memory.set_working("learning_backlog_v5", json.dumps(topics))

    def _push_top_to_learner(self):
        """Push the highest priority topics directly into the active learner queue."""
        topics = self._get_backlog()
        if not topics:
            return
            
        topics.sort(key=lambda x: x["priority"], reverse=True)
        top = topics.pop(0)
        self.learner.add_topic(top["topic"])
        self._save_backlog(topics)
