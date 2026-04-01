"""
rollback_controller.py - Rollback readiness policy for Jarvis self-improvement.
"""

from __future__ import annotations

from dataclasses import dataclass

from benchmarking.rollback_manager import RollbackManager


@dataclass
class RollbackPolicy:
    requires_backup_before_apply: bool = True
    requires_patch_log_entry: bool = True
    auto_revert_failed_candidates: bool = True
    destructive_mode_enabled: bool = False


class RollbackController:
    def __init__(self, db_path: str = "jarvis_brain.db"):
        self.policy = RollbackPolicy()
        self.manager = RollbackManager(db_path=db_path)

    def get_status(self) -> dict:
        return {
            "requires_backup_before_apply": self.policy.requires_backup_before_apply,
            "requires_patch_log_entry": self.policy.requires_patch_log_entry,
            "auto_revert_failed_candidates": self.policy.auto_revert_failed_candidates,
            "destructive_mode_enabled": self.policy.destructive_mode_enabled,
        }
