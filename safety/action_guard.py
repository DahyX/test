# -*- coding: utf-8 -*-
"""
action_guard.py — Top-Level Policy Enforcement
Intercepts execution flows that violate absolute system constraints before any logic touches the adapters.
"""

from tools.activepieces_models import ToolExecutionRequest

class ActionGuard:
    def __init__(self):
        self.hard_banned_scopes = ["local_status", "local_history", "self_improvement_request"]

    def is_execution_safely_permitted(self, request: ToolExecutionRequest) -> bool:
        """
        Absolute zero-tolerance check blocking backend execution for meta-questions.
        """
        # Rule 1: Never query SaaS workflows for local memory states
        if request.request_scope in self.hard_banned_scopes:
            return False
            
        # Rule 2: Do not route core CLI/desktop actions externally unless explicitly wrapped
        if request.tool_name == "bash" or request.tool_name == "desktop_mouse":
             return False
             
        # Allow default
        return True
