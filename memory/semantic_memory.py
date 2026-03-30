# -*- coding: utf-8 -*-
"""
semantic_memory.py — Handles durable facts, concepts, user profiles, and procedural heuristics.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from persistence.sqlite_store import SQLiteStore
from embeddings import EmbeddingEngine

class SemanticMemory:
    def __init__(self, db: SQLiteStore):
        self._db = db
        self.embedder = EmbeddingEngine()

    # ── Semantic Facts ────────────────────────────────────────────────────────
    def store_fact(self, url: str, topic: str, content: str, source_quality: float = 0.5, is_time_sensitive: bool = False) -> int:
        chunks = self.embedder.chunk_text(content)
        stored = 0
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 80: continue
            emb = self.embedder.embed(chunk)
            if not emb: continue
            
            # Basic deduplication (lazy check top 200)
            recent = self._db.fetch_all("SELECT embedding FROM semantic_memory ORDER BY id DESC LIMIT 200")
            is_dup = any(self.embedder.is_duplicate(emb, self.embedder.deserialize(r['embedding'])) 
                         for r in recent if r['embedding'])
            if is_dup: continue

            blob = self.embedder.serialize(emb)
            expires = (datetime.now() + timedelta(days=30)).isoformat() if is_time_sensitive else None
            
            self._db.execute("""
                INSERT INTO semantic_memory (url, topic, chunk_text, chunk_index, embedding, source_quality, is_time_sensitive, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (url, topic, chunk[:3000], i, blob, source_quality, 1 if is_time_sensitive else 0, expires, datetime.now().isoformat()))
            stored += 1
        return stored

    def search_facts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        query_vec = self.embedder.embed(query)
        if not query_vec: return []
        
        rows = self._db.fetch_all("SELECT * FROM semantic_memory")
        results = []
        now = datetime.now().isoformat()
        for r in rows:
            if r['is_time_sensitive'] and r['expires_at'] and r['expires_at'] < now:
                continue
            if not r['embedding']: continue
            
            stored_vec = self.embedder.deserialize(r['embedding'])
            sim = self.embedder.cosine_similarity(query_vec, stored_vec)
            if sim > 0.1:
                results.append({"text": r['chunk_text'], "similarity": sim, "topic": r['topic']})
                
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]

    # ── Profile Management ────────────────────────────────────────────────────
    def set_profile(self, key: str, value: str, category: str = "general", confidence: float = 0.5):
        self._db.execute("""
            INSERT INTO profile_memory (key, value, category, confidence, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, confidence = excluded.confidence, updated_at = excluded.updated_at
        """, (key, value, category, confidence, datetime.now().isoformat()))

    def get_profile(self) -> str:
        rows = self._db.fetch_all("SELECT key, value FROM profile_memory")
        if not rows: return ""
        lines = [f"- {r['key']}: {r['value']}" for r in rows]
        return "User Profile:\n" + "\n".join(lines)
        
    # ── Procedural Management ─────────────────────────────────────────────────
    def store_procedure(self, task_name: str, steps: str, app_context: str = ""):
        emb = self.embedder.embed(task_name + " " + steps)
        blob = self.embedder.serialize(emb) if emb else None
        now = datetime.now().isoformat()
        
        existing = self._db.fetch_one("SELECT id FROM procedural_memory WHERE task_name=?", (task_name,))
        if existing:
            self._db.execute("UPDATE procedural_memory SET steps=?, app_context=?, embedding=?, updated_at=? WHERE id=?", 
                             (steps, app_context, blob, now, existing['id']))
        else:
            self._db.execute("INSERT INTO procedural_memory (task_name, steps, app_context, embedding, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                             (task_name, steps, app_context, blob, now, now))

    def search_procedures(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        query_vec = self.embedder.embed(query)
        if not query_vec: return []
        
        rows = self._db.fetch_all("SELECT * FROM procedural_memory")
        results = []
        for r in rows:
            if not r['embedding']: continue
            sim = self.embedder.cosine_similarity(query_vec, self.embedder.deserialize(r['embedding']))
            if sim > 0.2:
                results.append({"task_name": r['task_name'], "steps": r['steps'], "similarity": sim})
                
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
