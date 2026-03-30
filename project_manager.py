# -*- coding: utf-8 -*-
"""
project_manager.py — Jarvis V5 Long-Term Project Memory
Tracks active efforts across sessions.
"""

import json
from datetime import datetime

class ProjectManager:
    def __init__(self, memory):
        self.memory = memory
        self.projects = self._load()

    def _load(self) -> dict:
        entry = self.memory.get_working("projects_v5")
        if entry:
            return json.loads(entry["value"])
        return {}

    def _save(self):
        self.memory.set_working("projects_v5", json.dumps(self.projects))

    def create_project(self, name: str, goal: str):
        self.projects[name] = {
            "goal": goal,
            "status": "in_progress",
            "tasks": [],
            "blockers": [],
            "files_touched": [],
            "updated_at": datetime.now().isoformat()
        }
        self._save()

    def update_status(self, name: str, status: str):
        if name in self.projects:
            self.projects[name]["status"] = status
            self.projects[name]["updated_at"] = datetime.now().isoformat()
            self._save()

    def add_task(self, name: str, task: str):
        if name in self.projects:
            if task not in self.projects[name]["tasks"]:
                self.projects[name]["tasks"].append(task)
                self.projects[name]["updated_at"] = datetime.now().isoformat()
                self._save()

    def get_active_projects(self) -> dict:
        return {k: v for k, v in self.projects.items() if v["status"] == "in_progress"}

    def get_context(self) -> str:
        """Return summarize project status for ContextBuilder."""
        active = self.get_active_projects()
        if not active:
            return ""
            
        lines = ["[Active Projects]"]
        for name, details in active.items():
            lines.append(f"Project: {name} | Goal: {details['goal']}")
            if details["tasks"]:
                lines.append(f"  Pending Tasks: {', '.join(details['tasks'])}")
        return "\n".join(lines)
