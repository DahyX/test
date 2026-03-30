# -*- coding: utf-8 -*-
"""
sqlite_store.py — Persistence layer for Jarvis V6 Database.
Handles raw connections, schema initialization, and generic queries.
Ensures backward compatibility with V5 tables.
"""

import sqlite3
from typing import List, Dict, Any, Tuple

DB_PATH = "jarvis_brain.db"

class SQLiteStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def fetch_one(self, query: str, params: tuple = ()) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else {}

    def execute(self, query: str, params: tuple = ()) -> int:
        with self._connect() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        with self._connect() as conn:
            conn.executemany(query, params_list)
            conn.commit()
            return len(params_list)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("PRAGMA synchronous=NORMAL")
            # Legacy
            conn.execute("CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, topic TEXT, content TEXT, keywords TEXT, learned_at TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS visited_urls (url TEXT PRIMARY KEY, visited_at TEXT)")
            
            # Semantic
            conn.execute("CREATE TABLE IF NOT EXISTS semantic_memory (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, topic TEXT, chunk_text TEXT, chunk_index INTEGER, embedding BLOB, source_quality REAL DEFAULT 0.5, is_time_sensitive INTEGER DEFAULT 0, expires_at TEXT, created_at TEXT)")
            
            # Episodic
            conn.execute("CREATE TABLE IF NOT EXISTS episodic_memory (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, topic TEXT, embedding BLOB, session_id TEXT, timestamp TEXT)")
            
            # Procedural
            conn.execute("CREATE TABLE IF NOT EXISTS procedural_memory (id INTEGER PRIMARY KEY AUTOINCREMENT, task_name TEXT, steps TEXT, app_context TEXT, success_count INTEGER DEFAULT 0, fail_count INTEGER DEFAULT 0, embedding BLOB, created_at TEXT, updated_at TEXT)")
            
            # Profile & Working
            conn.execute("CREATE TABLE IF NOT EXISTS profile_memory (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE, value TEXT, category TEXT, confidence REAL DEFAULT 0.5, updated_at TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS working_memory (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE, value TEXT, updated_at TEXT)")
            
            # Logs
            conn.execute("CREATE TABLE IF NOT EXISTS action_log (id INTEGER PRIMARY KEY AUTOINCREMENT, action_type TEXT, params TEXT, result TEXT, success INTEGER, timestamp TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS evaluation_log (id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, response TEXT, grounded INTEGER, answered INTEGER, confidence REAL, notes TEXT, timestamp TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS patch_log (id INTEGER PRIMARY KEY AUTOINCREMENT, patch_id TEXT, path TEXT, reason TEXT, diff TEXT, backup_path TEXT, status TEXT, created_at TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS self_improvement_log (id INTEGER PRIMARY KEY AUTOINCREMENT, goal TEXT, target_module TEXT, result TEXT, success INTEGER, notes TEXT, created_at TEXT)")

            conn.execute("CREATE INDEX IF NOT EXISTS idx_keywords ON knowledge(keywords)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_topic ON semantic_memory(topic)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episodic_session ON episodic_memory(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_profile_key ON profile_memory(key)")
            conn.commit()
