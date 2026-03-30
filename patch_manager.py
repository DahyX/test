# -*- coding: utf-8 -*-
"""
patch_manager.py — Safe Code Patch System
Applies, tracks, and rolls back code patches.
Every patch creates a backup first — no backup = no patch.
"""

import uuid
import json
from datetime import datetime
from codebase_manager import CodebaseManager


class PatchManager:
    """Manages code patches with full history and rollback support."""

    def __init__(self, codebase: CodebaseManager, memory=None):
        self.codebase = codebase
        self.memory = memory
        self._patch_history = []

    # ─────────────────────────────────────────────────────────────────────────
    #  APPLY PATCHES
    # ─────────────────────────────────────────────────────────────────────────
    def apply_full_rewrite(self, path: str, new_content: str, reason: str) -> dict:
        """Replace entire file content with new content."""
        # Read original
        old_content = self.codebase.read_file(path)
        if old_content.startswith("[Error]"):
            return self._fail(path, reason, f"Cannot read file: {old_content}")

        # Check editability
        abs_path = self.codebase._resolve_path(path)
        if not abs_path or not self.codebase.is_editable_path(abs_path):
            return self._fail(path, reason, f"Path not editable: {path}")

        # Create backup (MANDATORY)
        backup_path = self.codebase.backup_file(path)
        if not backup_path:
            return self._fail(path, reason, "Backup creation failed — aborting patch")

        # Generate diff
        diff = self.codebase.get_diff(old_content, new_content, path)
        diff_summary = self.codebase.get_diff_summary(diff)

        # Apply
        success = self.codebase.write_file(path, new_content)
        if not success:
            self.codebase.restore_backup(backup_path, path)
            return self._fail(path, reason, "Write failed — restored backup")

        # Record patch
        patch = self._record_patch(
            path=path, reason=reason, diff=diff,
            backup_path=backup_path, status="applied",
            diff_summary=diff_summary
        )

        print(f"[Patch] Applied: {path} ({diff_summary['total_changes']} line changes)")
        return patch

    def apply_targeted_patch(self, path: str, old_snippet: str,
                             new_snippet: str, reason: str) -> dict:
        """Replace a specific snippet within a file."""
        content = self.codebase.read_file(path)
        if content.startswith("[Error]"):
            return self._fail(path, reason, f"Cannot read: {content}")

        # Verify snippet exists
        if old_snippet not in content:
            return self._fail(path, reason,
                              f"Target snippet not found in {path}. "
                              f"Snippet: {old_snippet[:100]}...")

        # Count occurrences
        count = content.count(old_snippet)
        if count > 1:
            return self._fail(path, reason,
                              f"Snippet appears {count} times — ambiguous. "
                              f"Use apply_full_rewrite instead.")

        # Create backup
        backup_path = self.codebase.backup_file(path)
        if not backup_path:
            return self._fail(path, reason, "Backup failed — aborting")

        # Apply replacement
        new_content = content.replace(old_snippet, new_snippet, 1)
        diff = self.codebase.get_diff(content, new_content, path)
        diff_summary = self.codebase.get_diff_summary(diff)

        success = self.codebase.write_file(path, new_content)
        if not success:
            self.codebase.restore_backup(backup_path, path)
            return self._fail(path, reason, "Write failed — restored backup")

        patch = self._record_patch(
            path=path, reason=reason, diff=diff,
            backup_path=backup_path, status="applied",
            diff_summary=diff_summary
        )

        print(f"[Patch] Targeted patch applied: {path}")
        return patch

    # ─────────────────────────────────────────────────────────────────────────
    #  ROLLBACK
    # ─────────────────────────────────────────────────────────────────────────
    def rollback(self, patch_id: str) -> bool:
        """Rollback a specific patch by restoring its backup."""
        patch = self._find_patch(patch_id)
        if not patch:
            print(f"[Patch] Patch not found: {patch_id}")
            return False

        if patch["status"] == "rolled_back":
            print(f"[Patch] Already rolled back: {patch_id}")
            return False

        backup_path = patch.get("backup_path", "")
        if not backup_path:
            print(f"[Patch] No backup found for: {patch_id}")
            return False

        success = self.codebase.restore_backup(backup_path, patch["path"])
        if success:
            patch["status"] = "rolled_back"
            self._update_patch_in_memory(patch)
            print(f"[Patch] Rolled back: {patch_id} ({patch['path']})")
            return True

        print(f"[Patch] Rollback failed for: {patch_id}")
        return False

    def rollback_last(self) -> dict:
        """Rollback the most recent applied patch."""
        for patch in reversed(self._patch_history):
            if patch["status"] == "applied":
                success = self.rollback(patch["patch_id"])
                return {"success": success, "patch": patch}
        return {"success": False, "error": "No applied patches to rollback"}

    # ─────────────────────────────────────────────────────────────────────────
    #  VERIFY
    # ─────────────────────────────────────────────────────────────────────────
    def mark_verified(self, patch_id: str):
        """Mark a patch as verified (tests passed)."""
        patch = self._find_patch(patch_id)
        if patch:
            patch["status"] = "verified"
            self._update_patch_in_memory(patch)

    def mark_failed(self, patch_id: str):
        """Mark a patch as failed (tests failed, will be rolled back)."""
        patch = self._find_patch(patch_id)
        if patch:
            patch["status"] = "failed"
            self._update_patch_in_memory(patch)
            self.rollback(patch_id)

    # ─────────────────────────────────────────────────────────────────────────
    #  HISTORY
    # ─────────────────────────────────────────────────────────────────────────
    def get_patch_history(self, limit: int = 20) -> list:
        """Get recent patch history."""
        return self._patch_history[-limit:]

    def get_last_patch(self) -> dict:
        """Get the most recent patch."""
        return self._patch_history[-1] if self._patch_history else {}

    def format_patch_info(self, patch: dict) -> str:
        """Format a patch for display to the user."""
        if not patch:
            return "No patches found."
        summary = patch.get("diff_summary", {})
        return (
            f"Patch: {patch.get('patch_id', 'unknown')}\n"
            f"File: {patch.get('path', 'unknown')}\n"
            f"Reason: {patch.get('reason', 'unknown')}\n"
            f"Status: {patch.get('status', 'unknown')}\n"
            f"Changes: +{summary.get('lines_added', 0)} / "
            f"-{summary.get('lines_removed', 0)} lines\n"
            f"Time: {patch.get('created_at', 'unknown')}\n"
            f"Rollback: {'available' if patch.get('backup_path') else 'not available'}\n"
            f"\nDiff:\n{patch.get('diff', 'N/A')[:1000]}"
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  INTERNAL
    # ─────────────────────────────────────────────────────────────────────────
    def _record_patch(self, path: str, reason: str, diff: str,
                      backup_path: str, status: str, diff_summary: dict = None) -> dict:
        patch = {
            "patch_id": f"patch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            "path": path,
            "reason": reason,
            "diff": diff,
            "backup_path": backup_path,
            "status": status,
            "diff_summary": diff_summary or {},
            "created_at": datetime.now().isoformat(),
        }
        self._patch_history.append(patch)

        # Persist to memory
        if self.memory:
            try:
                self.memory.log_patch(
                    patch["patch_id"], path, reason,
                    diff[:5000], backup_path, status
                )
            except Exception as e:
                print(f"[Patch] Memory log failed: {e}")

        return patch

    def _find_patch(self, patch_id: str) -> dict:
        for p in self._patch_history:
            if p["patch_id"] == patch_id:
                return p
        return None

    def _update_patch_in_memory(self, patch: dict):
        if self.memory:
            try:
                self.memory.log_patch(
                    patch["patch_id"], patch["path"], patch["reason"],
                    patch.get("diff", "")[:5000], patch.get("backup_path", ""),
                    patch["status"]
                )
            except Exception:
                pass

    def _fail(self, path: str, reason: str, error: str) -> dict:
        print(f"[Patch] FAILED: {error}")
        patch = {
            "patch_id": f"fail_{uuid.uuid4().hex[:6]}",
            "path": path,
            "reason": reason,
            "status": "failed",
            "error": error,
            "created_at": datetime.now().isoformat(),
        }
        self._patch_history.append(patch)
        return patch
