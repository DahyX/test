# -*- coding: utf-8 -*-
"""
change_history.py — Local State Ledger
Provides an absolute local source of truth for "Did you work on any files?" 
Avoids prompting LLMs to guess system status.
"""

import datetime
from typing import List, Optional
from core.routing_models import ChangeRecord, ImprovementRecord, LocalStatusSummary

class ChangeHistoryStore:
    def __init__(self):
        # TODO: Persist to sqlite_store instead of transient memory
        self.changes: List[ChangeRecord] = []
        self.improvements: List[ImprovementRecord] = []

    def log_change(self, action_type: str, target_file: str, status: str, reason: str):
        record = ChangeRecord(
            timestamp=datetime.datetime.now().isoformat(),
            action_type=action_type,
            target_file=target_file,
            status=status,
            reason=reason
        )
        self.changes.append(record)

    def log_improvement(self, candidate_name: str, target: str, status: str, summary: str):
        record = ImprovementRecord(
            timestamp=datetime.datetime.now().isoformat(),
            candidate_name=candidate_name,
            target=target,
            status=status,
            result_summary=summary
        )
        self.improvements.append(record)
        
    def generate_status_summary(self) -> LocalStatusSummary:
        """Determines the exact plain-text reality of what happened in this session."""
        summary = LocalStatusSummary()
        summary.modified_files = list(set([c.target_file for c in self.changes if c.status == "success"]))
        summary.successful_changes = len([c for c in self.changes if c.status == "success"])
        summary.failed_changes = len([c for c in self.changes if c.status == "failed"])
        
        # Last 3 notes
        recent = sorted(self.changes, key=lambda x: x.timestamp, reverse=True)[:3]
        summary.recent_attempts = [f"{c.action_type} on {c.target_file}: {c.status}" for c in recent]
        
        return summary
