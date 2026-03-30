# -*- coding: utf-8 -*-
"""
safety_gate.py — Protects off-limits files and restricts high-risk actions.
"""

from core.runtime_state import ActionCandidate
import os
import json

class SafetyGate:
    def __init__(self):
        # The ultimate hardcoded allowlist for self_improvement patches (Phase 2):
        self.allowed_patch_scopes = [
            "reasoning/intent_analyzer.py",
            "perception/signal_extractor.py",
            "action/experimental_actions.py"
        ]
        
        # Absolute blocklist for execution:
        self.blocked_commands = [
            "rm -rf", "del /s /q", "format c:", "drop table"
        ]

    def is_safe(self, action: ActionCandidate) -> bool:
        """
        Evaluate risk level and hard constraints.
        Returns True if the action can execute immediately.
        Returns False if blocked or needs confirmation.
        """
        if action.risk_level == "high":
            print(f"⛔ [SAFETY GATE] Action '{action.tool_name}' blocked due to HIGH risk.")
            return False
            
        if action.tool_name == "desktop":
            cmd = action.params.get("cmd", "").lower()
            if any(evil in cmd for evil in self.blocked_commands):
                print(f"⛔ [SAFETY GATE] Dangerous command string detected.")
                return False
                
        if action.tool_name == "self_improve":
            # Check the target file
            target = action.params.get("target_file", "")
            if target not in self.allowed_patch_scopes:
                print(f"⛔ [SAFETY GATE] Patching '{target}' is outside the allowed sandbox!")
                return False

        return True
