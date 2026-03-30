# -*- coding: utf-8 -*-
"""
working_memory.py — Short-lived active runtime context.
Tracks active projects, ongoing multi-step plans, and pending confirmations.
"""

from persistence.sqlite_store import SQLiteStore
import json

class WorkingMemory:
    def __init__(self, db: SQLiteStore):
        self._db = db

    def get_state(self, key: str) -> dict:
        """Fetch a temporary value."""
        row = self._db.fetch_one("SELECT value FROM working_memory WHERE key=?", (key,))
        if row and row['value']:
            try:
                return json.loads(row['value'])
            except json.JSONDecodeError:
                return {"value": row['value']}
        return {}

    def set_state(self, key: str, value: dict):
        """Store a temporary dictionary."""
        val_str = json.dumps(value)
        self._db.execute("INSERT OR REPLACE INTO working_memory (key, value) VALUES (?, ?)", (key, val_str))

    def clear_state(self, key: str):
        """Delete temporary state."""
        self._db.execute("DELETE FROM working_memory WHERE key=?", (key,))

    def get_pending_confirmation(self) -> dict:
        """Returns details if an action is awaiting YES/NO from user."""
        return self.get_state("pending_confirmation")
        
    def set_pending_confirmation(self, action_candidate: dict):
        self.set_state("pending_confirmation", action_candidate)
        
    def clear_pending_confirmation(self):
        self.clear_state("pending_confirmation")

    def build_context_string(self) -> str:
        """Returns a summarized view of working memory for the LLM."""
        lines = []
        pending = self.get_pending_confirmation()
        if pending:
            lines.append(f"PENDING USER CONFIRMATION: {pending.get('tool_name')} ({pending.get('params')})")
            
        active_plan = self.get_state("active_plan")
        if active_plan:
            lines.append(f"ACTIVE GOAL: {active_plan.get('goal')}")
            
        user_info = self.get_state("user_v6")
        if user_info and user_info.get("name"):
            lines.append(f"USER: {user_info.get('name')}")
            
        return "\n".join(lines).strip()
