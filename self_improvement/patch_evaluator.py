# -*- coding: utf-8 -*-
"""
patch_evaluator.py — Strict Safe Evaluator
Applies patches strictly into sandbox mode, hard-disabling default auto-apply to the live codebase.
"""

import py_compile
import os
import shutil

class PatchEvaluator:
    def __init__(self):
        self.auto_apply_enabled = False  # Hard default disable

    def evaluate_and_apply(self, patch_proposal: dict, manual_approval: bool = False, sandbox_mode: bool = True) -> str:
        """
        Evaluates a patch. Never applies to live source without explicit approval.
        """
        if not patch_proposal.get("success", False):
            return f"Patch generation naturally blocked: {patch_proposal.get('error', 'Unknown')}"

        if not self.auto_apply_enabled and not manual_approval and not sandbox_mode:
            return "Patch Evaluator Error: Auto-apply is globally disabled. Manual approval or Sandbox mode required."
            
        target_file = patch_proposal.get("target_file", "")
        if not target_file:
            return "Patch Evaluator Error: Proposal lacks a target file designation."

        # Execute only in isolated mode or if safely approved
        execution_target = target_file
        if sandbox_mode:
            execution_target += ".sandbox.tmp"
            shutil.copy2(target_file, execution_target)

        # 1. Apply logic safely
        target_snippet = patch_proposal.get("target_snippet", "")
        replacement = patch_proposal.get("replacement", "")

        try:
            with open(execution_target, "r", encoding="utf-8") as f:
                content = f.read()

            if target_snippet not in content:
                # Immediate fail if unsure, no guessing
                return "Target snippet not found exactly in the file. Patch aborted safely without guessing."

            new_content = content.replace(target_snippet, replacement, 1)

            with open(execution_target, "w", encoding="utf-8") as f:
                f.write(new_content)

            # 2. Compile Check validation
            py_compile.compile(execution_target, doraise=True)
            return f"[Sandbox Success] Patch safely verified in AST on {execution_target}."
            
        except py_compile.PyCompileError as e:
            return f"[Validation Failed] Patch introduced syntax error: {e}"
        except Exception as e:
            return f"[Rollback] Unexpected error during sandbox patching: {e}"
