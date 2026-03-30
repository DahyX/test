# -*- coding: utf-8 -*-
"""
user_model.py — Jarvis V5 Long-Term User Memory
Stores stable facts about the user to personalize the assistant.
"""

import json
from datetime import datetime

class UserModel:
    def __init__(self, memory):
        self.memory = memory
        self.profile = self._load()

    def _load(self) -> dict:
        entry = self.memory.get_working("user_model_v5")
        if entry:
            return json.loads(entry["value"])
        return {
            "name": None,
            "preferences": {},
            "tone": "natural",
            "interests": []
        }

    def _save(self):
        self.memory.set_working("user_model_v5", json.dumps(self.profile))

    def update_preference(self, key: str, value: str):
        """Set a user preference (e.g. 'theme', 'dark')."""
        self.profile["preferences"][key] = value
        self._save()

    def get_preference(self, key: str) -> str:
        return self.profile["preferences"].get(key)
        
    def set_name(self, name: str):
        self.profile["name"] = name
        self._save()
        
    def get_name(self) -> str:
        return self.profile["name"]
        
    def get_context(self) -> str:
        """Return a string summary of the user for the ContextBuilder."""
        lines = []
        if self.profile["name"]:
            lines.append(f"User Name: {self.profile['name']}")
        if self.profile["preferences"]:
            lines.append(f"Preferences: {json.dumps(self.profile['preferences'])}")
        if self.profile["tone"]:
            lines.append(f"Preferred Tone: {self.profile['tone']}")
        return "\n".join(lines)
