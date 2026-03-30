# -*- coding: utf-8 -*-
"""
episodic_memory.py — Handles conversation histories, event logs, and sequence recalling.
"""

from datetime import datetime
from typing import List, Dict, Any
from persistence.sqlite_store import SQLiteStore
from embeddings import EmbeddingEngine

class EpisodicMemory:
    def __init__(self, db: SQLiteStore):
        self._db = db
        self.embedder = EmbeddingEngine()

    def save_episode(self, role: str, content: str, topic: str = "", session_id: str = "default"):
        """Save a discrete event or conversational turn."""
        emb = self.embedder.embed(content) if role in ("user", "action") else []
        blob = self.embedder.serialize(emb) if emb else None
        
        self._db.execute("""
            INSERT INTO episodic_memory (role, content, topic, embedding, session_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (role, content[:3000], topic, blob, session_id, datetime.now().isoformat()))

    def get_recent(self, limit: int = 20, session_id: str = None) -> List[Dict[str, str]]:
        if session_id:
            rows = self._db.fetch_all("SELECT role, content FROM episodic_memory WHERE session_id=? ORDER BY id DESC LIMIT ?", (session_id, limit))
        else:
            rows = self._db.fetch_all("SELECT role, content FROM episodic_memory ORDER BY id DESC LIMIT ?", (limit,))
        return [{"role": r['role'], "content": r['content']} for r in reversed(rows)]

    def search_episodes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_vec = self.embedder.embed(query)
        if not query_vec: return []

        rows = self._db.fetch_all("SELECT role, content, topic, embedding FROM episodic_memory WHERE embedding IS NOT NULL")
        results = []
        
        for r in rows:
            stored_vec = self.embedder.deserialize(r['embedding'])
            if not stored_vec: continue
            sim = self.embedder.cosine_similarity(query_vec, stored_vec)
            if sim > 0.2:
                results.append({"role": r['role'], "content": r['content'], "topic": r['topic'], "similarity": sim})
                
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
        
    def log_action(self, action_type: str, params: str, result: str, success: bool):
        self._db.execute("INSERT INTO action_log (action_type, params, result, success, timestamp) VALUES (?, ?, ?, ?, ?)",
                         (action_type, params, result, 1 if success else 0, datetime.now().isoformat()))
