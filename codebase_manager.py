# -*- coding: utf-8 -*-
"""
codebase_manager.py — Safe Project File Manager
Handles reading, writing, backing up, and diffing project files.
Enforces strict safety rules on what can be edited.
"""

import os
import shutil
import difflib
import glob
from datetime import datetime
from typing import Optional


# ── Safety Configuration ─────────────────────────────────────────────────────
EDITABLE_EXTENSIONS = {".py", ".json", ".yaml", ".yml", ".toml", ".md", ".txt", ".cfg", ".ini"}

BLOCKED_PATHS = [
    "jarvis_brain.db",
    "__pycache__",
    ".git",
    ".env",
    "node_modules",
    "venv",
    ".venv",
    "screenshots",
    "backups",
]

BLOCKED_PATTERNS = [
    "*.pyc", "*.pyo", "*.exe", "*.dll", "*.so", "*.dylib",
    "*.db", "*.sqlite", "*.sqlite3",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp",
    "*.zip", "*.tar", "*.gz", "*.7z",
    "*.bin", "*.dat",
]


class CodebaseManager:
    """Safe project file manager with backup and diff support."""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.backup_dir = os.path.join(self.project_root, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        print(f"[Codebase] Project root: {self.project_root}")

    # ─────────────────────────────────────────────────────────────────────────
    #  FILE ENUMERATION
    # ─────────────────────────────────────────────────────────────────────────
    def list_project_files(self, root: str = None) -> list:
        """List all editable project files."""
        root = root or self.project_root
        files = []
        for dirpath, dirnames, filenames in os.walk(root):
            # Skip blocked directories
            dirnames[:] = [d for d in dirnames if d not in BLOCKED_PATHS
                           and not d.startswith(".")]
            rel_dir = os.path.relpath(dirpath, root)

            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                rel_path = os.path.join(rel_dir, fname) if rel_dir != "." else fname

                if self.is_editable_path(fpath):
                    size = os.path.getsize(fpath)
                    files.append({
                        "path": rel_path,
                        "abs_path": fpath,
                        "size": size,
                        "extension": os.path.splitext(fname)[1],
                    })
        return files

    # ─────────────────────────────────────────────────────────────────────────
    #  READ / WRITE
    # ─────────────────────────────────────────────────────────────────────────
    def read_file(self, path: str) -> str:
        """Read file contents. Path can be relative to project root."""
        abs_path = self._resolve_path(path)
        if not abs_path:
            return f"[Error] Cannot read: path not found or not editable: {path}"
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            return f"[Error] Failed to read {path}: {e}"

    def write_file(self, path: str, content: str) -> bool:
        """Write content to file. Must be an editable path."""
        abs_path = self._resolve_path(path)
        if not abs_path:
            print(f"[Codebase] Write blocked: {path}")
            return False
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[Codebase] Write failed: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    #  BACKUP / RESTORE
    # ─────────────────────────────────────────────────────────────────────────
    def backup_file(self, path: str) -> str:
        """Create a timestamped backup of a file. Returns backup path."""
        abs_path = self._resolve_path(path)
        if not abs_path or not os.path.exists(abs_path):
            return ""

        basename = os.path.basename(abs_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{basename}.{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_name)

        try:
            shutil.copy2(abs_path, backup_path)
            print(f"[Codebase] Backup created: {backup_name}")
            return backup_path
        except Exception as e:
            print(f"[Codebase] Backup failed: {e}")
            return ""

    def restore_backup(self, backup_path: str, original_path: str) -> bool:
        """Restore a file from backup."""
        abs_original = self._resolve_path(original_path)
        if not abs_original:
            return False
        if not os.path.exists(backup_path):
            print(f"[Codebase] Backup not found: {backup_path}")
            return False
        try:
            shutil.copy2(backup_path, abs_original)
            print(f"[Codebase] Restored: {original_path}")
            return True
        except Exception as e:
            print(f"[Codebase] Restore failed: {e}")
            return False

    def list_backups(self, filename: str = None) -> list:
        """List all backups, optionally filtered by filename."""
        backups = []
        if not os.path.exists(self.backup_dir):
            return backups
        for f in sorted(os.listdir(self.backup_dir), reverse=True):
            if filename and not f.startswith(filename):
                continue
            fpath = os.path.join(self.backup_dir, f)
            backups.append({
                "filename": f,
                "path": fpath,
                "size": os.path.getsize(fpath),
                "modified": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
            })
        return backups

    # ─────────────────────────────────────────────────────────────────────────
    #  DIFF
    # ─────────────────────────────────────────────────────────────────────────
    def get_diff(self, old_text: str, new_text: str, path: str = "file") -> str:
        """Generate unified diff between old and new content."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{path}", tofile=f"b/{path}",
            lineterm=""
        )
        return "\n".join(diff)

    def get_diff_summary(self, diff_text: str) -> dict:
        """Summarize a diff: lines added, removed, changed."""
        added = sum(1 for l in diff_text.split("\n") if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff_text.split("\n") if l.startswith("-") and not l.startswith("---"))
        return {"lines_added": added, "lines_removed": removed, "total_changes": added + removed}

    # ─────────────────────────────────────────────────────────────────────────
    #  SAFETY CHECKS
    # ─────────────────────────────────────────────────────────────────────────
    def is_editable_path(self, path: str) -> bool:
        """Check if a path is safe to edit."""
        abs_path = os.path.abspath(path)

        # Must be within project root
        if not abs_path.startswith(os.path.abspath(self.project_root)):
            return False

        basename = os.path.basename(abs_path)
        ext = os.path.splitext(basename)[1].lower()

        # Check extension
        if ext not in EDITABLE_EXTENSIONS:
            return False

        # Check blocked paths
        rel = os.path.relpath(abs_path, self.project_root)
        for blocked in BLOCKED_PATHS:
            if blocked in rel:
                return False

        # Check blocked patterns
        for pattern in BLOCKED_PATTERNS:
            if glob.fnmatch.fnmatch(basename, pattern):
                return False

        return True

    def search_code(self, query: str, paths: list = None) -> list:
        """Search for text in project files. Returns matching lines."""
        results = []
        files = paths or [f["abs_path"] for f in self.list_project_files()]

        query_lower = query.lower()
        for fpath in files:
            if isinstance(fpath, dict):
                fpath = fpath.get("abs_path", fpath.get("path", ""))
            abs_path = self._resolve_path(fpath)
            if not abs_path:
                continue
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if query_lower in line.lower():
                            results.append({
                                "file": os.path.relpath(abs_path, self.project_root),
                                "line": i,
                                "content": line.rstrip(),
                            })
            except Exception:
                continue

        return results[:50]  # Cap results

    # ─────────────────────────────────────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────────────────────────────────────
    def _resolve_path(self, path: str) -> Optional[str]:
        """Resolve a path to absolute, validating it's within project scope."""
        if not path:
            return None
        if os.path.isabs(path):
            abs_path = path
        else:
            abs_path = os.path.join(self.project_root, path)
        abs_path = os.path.abspath(abs_path)

        if not abs_path.startswith(os.path.abspath(self.project_root)):
            return None
        if not self.is_editable_path(abs_path) and os.path.exists(abs_path):
            # Allow reading non-editable files, block writing
            return abs_path
        return abs_path


if __name__ == "__main__":
    cm = CodebaseManager()
    files = cm.list_project_files()
    print(f"Found {len(files)} editable files:")
    for f in files:
        print(f"  {f['path']} ({f['size']} bytes)")
