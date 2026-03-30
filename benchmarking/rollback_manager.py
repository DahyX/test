# -*- coding: utf-8 -*-
"""
rollback_manager.py — Safely reverts applied patches and state changes if regressions occur.
"""

from persistence.sqlite_store import SQLiteStore
import os
import shutil

class RollbackManager:
    def __init__(self, db_path: str = "jarvis_brain.db"):
        self.db = SQLiteStore(db_path)

    def revert_patch(self, patch_id: str) -> bool:
        """
        Reverts a specific file modification using the saved patch_id.
        Phase 2 implementation.
        """
        print(f"[RollbackManager] Attempting to revert patch {patch_id}...")
        log = self.db.fetch_one("SELECT * FROM patch_log WHERE patch_id=?", (patch_id,))
        if not log:
            print("[RollbackManager] Patch not found in logs.")
            return False
            
        backup_path = log.get("backup_path")
        target_path = log.get("path")
        
        if backup_path and os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, target_path)
                print(f"[RollbackManager] Successfully reverted {target_path} from backup.")
                self.db.execute("UPDATE patch_log SET status='reverted' WHERE patch_id=?", (patch_id,))
                return True
            except Exception as e:
                print(f"[RollbackManager] File revert failed: {e}")
                return False
                
        print("[RollbackManager] Backup file missing or invalid.")
        return False
        
    def rollback_latest_state(self):
        """Reverts the last action transaction sequence."""
        # TODO: Implement atomic SQL transactions for Phase 2 Rollbacks.
        pass
