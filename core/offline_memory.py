# -*- coding: utf-8 -*-
"""
offline_memory.py - Durable local memory for Jarvis.

This layer is intentionally offline-first. It uses the existing SQLite store
but avoids depending on remote APIs so Jarvis can still remember context,
conversation history, and working notes when model backends are unavailable.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from typing import Dict, List

from persistence.sqlite_store import SQLiteStore


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "our", "the",
    "this", "to", "what", "when", "where", "which", "who", "why", "with",
    "you", "your",
}


class OfflineMemory:
    def __init__(self, db_path: str = "jarvis_brain.db", session_id: str = "jarvis_runtime"):
        self.db = SQLiteStore(db_path)
        self.session_id = session_id

    def stats(self) -> dict:
        with self.db._connect() as conn:
            semantic_count = conn.execute("SELECT COUNT(*) FROM semantic_memory").fetchone()[0]
            episodic_count = conn.execute("SELECT COUNT(*) FROM episodic_memory").fetchone()[0]
            procedural_count = conn.execute("SELECT COUNT(*) FROM procedural_memory").fetchone()[0]
            working_count = conn.execute("SELECT COUNT(*) FROM working_memory").fetchone()[0]
            profile_count = conn.execute("SELECT COUNT(*) FROM profile_memory").fetchone()[0]

        return {
            "total_facts": semantic_count + profile_count,
            "semantic_chunks": semantic_count,
            "urls_visited": 0,
            "episodes": episodic_count,
            "procedures": procedural_count,
            "working_items": working_count,
            "profile_items": profile_count,
        }

    def remember_turn(self, role: str, content: str, topic: str = "") -> None:
        text = (content or "").strip()
        if not text:
            return

        derived_topic = topic or self._extract_topic(text)
        self.db.execute(
            """
            INSERT INTO episodic_memory (role, content, topic, embedding, session_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (role, text[:3000], derived_topic[:200], None, self.session_id, datetime.now().isoformat()),
        )

    def remember_exchange(self, user_text: str, assistant_text: str, topic: str = "") -> None:
        shared_topic = topic or self._extract_topic(user_text)
        self.remember_turn("user", user_text, shared_topic)
        self.remember_turn("assistant", assistant_text, shared_topic)

    def get_recent_episodes(self, limit: int = 50) -> List[Dict[str, str]]:
        rows = self.db.fetch_all(
            """
            SELECT role, content, topic, session_id, timestamp
            FROM episodic_memory
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return list(reversed(rows))

    def search_episodes(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        tokens = self._tokenize(query)
        if not tokens:
            return self.get_recent_episodes(limit)

        rows = self.db.fetch_all(
            """
            SELECT role, content, topic, session_id, timestamp
            FROM episodic_memory
            ORDER BY id DESC
            LIMIT 250
            """
        )

        scored = []
        for row in rows:
            haystack = f"{row.get('topic', '')} {row.get('content', '')}".lower()
            overlap = sum(1 for token in tokens if token in haystack)
            if overlap == 0:
                continue
            scored.append((overlap, row))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [row for _, row in scored[:limit]]

    def build_chat_context(self, query: str, limit: int = 4) -> str:
        hits = self.search_episodes(query, limit=limit)
        if not hits:
            return ""

        lines = []
        for hit in hits:
            role = hit.get("role", "system")
            content = hit.get("content", "").strip()
            if not content:
                continue
            lines.append(f"{role}: {content[:240]}")
        return "\n".join(lines)

    def set_working(self, key: str, value) -> None:
        payload = value if isinstance(value, str) else json.dumps(value)
        self.db.execute(
            """
            INSERT OR REPLACE INTO working_memory (key, value, updated_at)
            VALUES (?, ?, ?)
            """,
            (key, payload, datetime.now().isoformat()),
        )

    def get_working(self, key: str) -> dict:
        row = self.db.fetch_one("SELECT value FROM working_memory WHERE key=?", (key,))
        raw = row.get("value")
        if raw is None:
            return {}
        try:
            return {"value": json.loads(raw)}
        except json.JSONDecodeError:
            return {"value": raw}

    def get_working_value(self, key: str, default=None):
        value = self.get_working(key).get("value")
        return default if value is None else value

    def _extract_topic(self, text: str) -> str:
        tokens = self._tokenize(text)
        if not tokens:
            return "general"
        counts = Counter(tokens)
        return " ".join(token for token, _ in counts.most_common(4))

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9_./-]+", " ", (text or "").lower())
        return [token for token in cleaned.split() if len(token) > 2 and token not in STOP_WORDS]
