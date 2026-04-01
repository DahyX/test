# -*- coding: utf-8 -*-
"""
change_history.py — Local History Store
Simple JSON-backed store to track local changes and patch attempts safely.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from core.routing_models import ChangeRecord, ImprovementRecord, LocalStatusSummary

HISTORY_FILE = ".jarvis_history.json"

class ChangeHistoryStore:
    def __init__(self, filepath: str = HISTORY_FILE):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not os.path.exists(self.filepath):
            try:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump({"changes": [], "improvements": []}, f)
            except IOError:
                pass

    def _read_data(self) -> Dict[str, Any]:
        if not os.path.exists(self.filepath):
            return {"changes": [], "improvements": []}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {"changes": [], "improvements": []}

    def _write_data(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass

    def record_file_modification(self, target_file: str, status: str, reason: str, session_id: str = "local_session") -> None:
        data = self._read_data()
        record = ChangeRecord(
            timestamp=datetime.utcnow().isoformat(),
            action_type="file_modification",
            target_file=target_file,
            status=status,
            reason=reason,
            session_id=session_id
        )
        data["changes"].append(record.__dict__)
        self._write_data(data)

    def record_improvement_attempt(self, candidate_name: str, target: str, status: str, result_summary: str, session_id: str = "local_session") -> None:
        data = self._read_data()
        record = ImprovementRecord(
            timestamp=datetime.utcnow().isoformat(),
            candidate_name=candidate_name,
            target=target,
            status=status,
            result_summary=result_summary,
            session_id=session_id
        )
        data["improvements"].append(record.__dict__)
        self._write_data(data)

    def get_local_status_summary(self) -> LocalStatusSummary:
        data = self._read_data()
        summary = LocalStatusSummary()
        for c in data.get("changes", []):
            if c.get("status") == "success":
                summary.successful_changes += 1
                if c.get("target_file") not in summary.modified_files:
                    summary.modified_files.append(c["target_file"])
            else:
                summary.failed_changes += 1
            summary.recent_attempts.append(f"{c.get('action_type')} on {c.get('target_file')}: {c.get('status')}")
        
        summary.recent_attempts = summary.recent_attempts[-10:]
        return summary

    def get_history_summary(self) -> str:
        data = self._read_data()
        lines = ["Improvement and Change History:"]
        for c in data.get("improvements", [])[-5:]:
            lines.append(f"- {c.get('timestamp')}: {c.get('candidate_name')} -> {c.get('target')} [{c.get('status')}]")
        for c in data.get("changes", [])[-5:]:
            lines.append(f"- {c.get('timestamp')}: modified {c.get('target_file')} [{c.get('status')}]")
        
        if len(lines) == 1:
            return "No local history found."
        return "\n".join(lines)
