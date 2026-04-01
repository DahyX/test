# -*- coding: utf-8 -*-
"""
patch_proposer.py — Safe Patch Proposal Wrapper
Defines strict rules requiring target verification prior to AI patch logic execution.
"""

import os
from typing import Dict

class PatchProposer:
    ALLOWLIST_DIRS = ["core/", "reasoning/", "self_improvement/", "tests/"]

    def propose_patch(self, instruction: str, target_file: str) -> Dict[str, str]:
        """Propose a patch but never execute or assume target."""
        if not target_file:
            return {"error": "Missing explicit target file. Refusing to guess."}

        target_file_normalized = target_file.replace("\\", "/")
        is_allowed = any(target_file_normalized.startswith(d) for d in self.ALLOWLIST_DIRS)
        
        if not is_allowed:
            return {"error": f"Target file '{target_file}' is not in the allowlist."}

        if not os.path.exists(target_file):
            return {"error": f"Target file '{target_file}' does not exist. Failing safely."}

        # Proposal filler wrapper logic returning safe struct outputs
        return {
            "status": "proposed",
            "target": target_file,
            "proposal": f"Proposed hypothetical patch string driven entirely safely against: {instruction}"
        }
