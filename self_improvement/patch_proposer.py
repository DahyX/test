# -*- coding: utf-8 -*-
"""
patch_proposer.py — Safe proposal constraint wrapper
Overrides vague patches. Always fails safely if vague.
"""

import os
import re

class PatchProposer:
    def __init__(self, model: str = "qwen2.5-coder:1.5b"):
        self.model = model
        self.allowlist = [
            "reasoning/intent_analyzer.py",
            "perception/signal_extractor.py",
        ]

    def propose_patch(self, instruction: str) -> dict:
        """
        Generates a proposal ONLY if a valid target file is strictly defined in the prompt.
        Defaults to proposal-only behavior.
        """
        # 1. Enforce Explicit Target File Requirement
        target_file = None
        for module in self.allowlist:
            if module in instruction:
                target_file = module
                break
                
        # Also check for .py regex
        py_match = re.search(r'([\w/]+\.py)', instruction)
        if py_match and not target_file:
            target_file = py_match.group(1)

        if not target_file:
            return {"success": False, "error": "Explicit target file required and missing from instruction."}

        if target_file not in self.allowlist:
            return {"success": False, "error": f"Target file '{target_file}' is protected and not in the Sandbox Allowlist."}

        if not os.path.exists(target_file):
            return {"success": False, "error": f"Target file '{target_file}' does not exist locally."}

        # 2. If safe, generate the proposal-only payload
        # Placeholder for LLM patch generation
        return {
            "success": True,
            "target_snippet": "# Replace me",
            "replacement": "# Replaced",
            "target_file": target_file,
            "reason": "Safe sandbox execution.",
            "mode": "proposal_only"  # Default configuration
        }
