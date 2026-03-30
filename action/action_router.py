# -*- coding: utf-8 -*-
"""
action_router.py — Routes validated ActionCandidates to their specific action modules.
"""

from core.runtime_state import ActionCandidate
from self_improvement.patch_proposer import PatchProposer
from self_improvement.patch_evaluator import PatchEvaluator
from action.desktop_actions import DesktopActions
from action.web_actions import WebActions
from action.code_actions import CodeActions

class ActionRouter:
    def __init__(self):
        print("[ActionRouter] Initializing execution sub-systems...")
        self.patch_proposer = PatchProposer()
        self.patch_evaluator = PatchEvaluator()
        self.desktop = DesktopActions()
        self.web = WebActions()
        self.code = CodeActions()
        
    def execute(self, action: ActionCandidate) -> str:
        """Execute the action and return the raw string result."""
        tool = action.tool_name
        params = action.params
        
        try:
            if tool == "respond":
                return params.get("text", "No response text found.")
                
            elif tool == "desktop":
                cmd = params.get("cmd")
                return self.desktop.execute(cmd, params)
                
            elif tool == "web":
                cmd = params.get("cmd", "read")
                return self.web.execute(cmd, params)
                
            elif tool == "read_code" or tool == "code":
                cmd = params.get("cmd", "search")
                return self.code.execute(cmd, params)
                
            elif tool == "self_improve":
                target = params.get("target_file")
                issue = params.get("issue_description", "Optimize this module.")
                print(f"[ActionRouter] Initiating self-improvement on {target}...")
                proposal = self.patch_proposer.propose_patch(target, issue)
                return self.patch_evaluator.evaluate_and_apply(target, proposal)
                
            else:
                return f"Tool '{tool}' is not recognized by the ActionRouter."
                
        except Exception as e:
            return f"Action execution failed: {e}"
