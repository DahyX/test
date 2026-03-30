# -*- coding: utf-8 -*-
"""
patch_evaluator.py — Applies proposed patches dynamically, tests them, and handles rollbacks.
"""

import py_compile
import os
import shutil

class PatchEvaluator:
    def __init__(self):
        pass

    def evaluate_and_apply(self, target_file: str, patch_proposal: dict) -> str:
        """
        Takes the proposed patch, safely applies it, checks syntax, and returns the result.
        """
        if "error" in patch_proposal:
            return f"Patch generation failed: {patch_proposal['error']}"

        target = patch_proposal.get("target_snippet", "")
        replacement = patch_proposal.get("replacement", "")

        if not target or not replacement:
            return "Invalid patch proposal format."

        # Backup the file
        backup_file = target_file + ".bak_v6_auto"
        shutil.copy2(target_file, backup_file)

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()

            if target not in content:
                # Naive fallback: try removing whitespace diffs
                return "Target snippet not found exactly in the file. Patch aborted safely."

            new_content = content.replace(target, replacement, 1)

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Compile Check
            try:
                py_compile.compile(target_file, doraise=True)
                return f"[Success] Patch applied to {target_file}. Syntax verified."
            except py_compile.PyCompileError as e:
                # Rollback on Syntax Error
                shutil.copy2(backup_file, target_file)
                return f"[Rollback] Patch introduced syntax error. Aborted."

        except Exception as e:
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, target_file)
            return f"[Rollback] Unexpected error during patching: {e}"
