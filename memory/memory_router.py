# -*- coding: utf-8 -*-
"""
memory_router.py — Unified V6 Memory Interface.
Wraps all modular memory components into a single access point for the rest of the system.
"""

from typing import Dict, Any, List
from persistence.sqlite_store import SQLiteStore
from memory.semantic_memory import SemanticMemory
from memory.episodic_memory import EpisodicMemory
from memory.working_memory import WorkingMemory

class MemoryRouter:
    """
    Coordinates between Working, Semantic, and Episodic memory stores.
    The primary interface used by ContextBuilder and ReflectionEngine.
    """
    def __init__(self, db_path: str = "jarvis_brain.db"):
        self.db = SQLiteStore(db_path)
        self.semantic = SemanticMemory(self.db)
        self.episodic = EpisodicMemory(self.db)
        self.working = WorkingMemory(self.db)

    def write_pending(self, memory_writes: List[Dict[str, Any]]):
        """
        Process batches of memory updates from the Reflection layer.
        Format expectation mapping:
        type="semantic" => store_fact
        type="episodic" => save_episode
        type="procedural" => store_procedure
        type="working" => set_state
        type="action_log" => log_action
        """
        for write in memory_writes:
            mem_type = write.get("type")
            data = write.get("data", {})
            try:
                if mem_type == "semantic":
                    self.semantic.store_fact(data.get("url", "reflection"), data.get("topic", ""), data.get("content", ""))
                elif mem_type == "episodic":
                    self.episodic.save_episode(data.get("role", "system"), data.get("content", ""), data.get("topic", ""))
                elif mem_type == "procedural":
                    self.semantic.store_procedure(data.get("task_name", ""), data.get("steps", ""))
                elif mem_type == "working":
                    if "key" in data and "value" in data:
                        self.working.set_state(data["key"], data["value"])
                elif mem_type == "action_log":
                    self.episodic.log_action(data.get("action_type", ""), data.get("params", ""), data.get("result", ""), data.get("success", False))
                elif mem_type == "profile":
                    self.semantic.set_profile(data.get("key", ""), data.get("value", ""))
            except Exception as e:
                print(f"[MemoryRouter] Failed to write {mem_type}: {e}")

    def query_context(self, query: str, limit: int = 5) -> Dict[str, str]:
        """Fetch unified context matching a query."""
        semantic_res = self.semantic.search_facts(query, limit)
        episodic_res = self.episodic.search_episodes(query, 3)
        procedural_res = self.semantic.search_procedures(query, 2)
        
        return {
            "semantic": "\n".join([r['text'] for r in semantic_res]),
            "episodic": "\n".join([f"{r['role']}: {r['content']}" for r in episodic_res]),
            "procedural": "\n".join([f"Procedure for '{r['task_name']}':\n{r['steps']}" for r in procedural_res])
        }

    # ── Legacy Compatibility for Edge Clients (Evaluator, Scheduler, WebServer)
    
    def stats(self) -> dict:
        with self.db._connect() as conn:
            c_facts = conn.execute("SELECT COUNT(*) FROM semantic_memory").fetchone()[0]
            c_epi = conn.execute("SELECT COUNT(*) FROM episodic_memory").fetchone()[0]
            c_proc = conn.execute("SELECT COUNT(*) FROM procedural_memory").fetchone()[0]
        return {
            "total_facts": c_facts,
            "semantic_chunks": c_facts,
            "urls_visited": 0,
            "episodes": c_epi,
            "procedures": c_proc,
            "legacy_facts": 0
        }
        
    def search_semantic(self, query: str, limit: int = 5):
        return self.semantic.search_facts(query, limit)
        
    def get_recent_episodes(self, limit: int = 50):
        # Empty query to get the latest based on SQLiteStore implementation
        return self.episodic.search_episodes("", limit)
        
    def log_evaluation(self, **kwargs):
        pass # Evaluations handled internally by ReflectionEngine in V6

    def log_action(self, action: str, params: str, result: str, success: bool):
        self.write_pending([{"type": "action_log", "data": {
            "action_type": action, "params": params, "result": result, "success": success
        }}])

    def set_working(self, key: str, value: str):
        self.working.set_state(key, value)
        
    def get_working(self, key: str) -> dict:
        return {"value": self.working.get_state(key)}
    
    def _connect(self):
        return self.db._connect()
