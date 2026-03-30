# -*- coding: utf-8 -*-
"""
tool_risk_policy.py — Execution Safety Filter
Calculates action damage potentials immediately after a tool request before allowing bridging to the backend.
"""

from tools.activepieces_models import ToolExecutionRequest, ToolRiskAssessment

class ToolRiskPolicy:
    def __init__(self):
        # Immediate block heuristics
        self.destructive_words = ["delete", "drop", "purge", "rm -rf", "format"]
        self.broadcast_tools = ["email_summary", "slack_post", "tweet_post"]

    def assess(self, request: ToolExecutionRequest) -> ToolRiskAssessment:
        """Generates a mathematical risk assessment enforcing manual approvals."""
        
        # 1. Deny strictly dangerous params
        params_str = str(request.parameters).lower()
        if any(w in params_str for w in self.destructive_words):
            return ToolRiskAssessment(
                risk_level="critical",
                requires_approval=True,
                allowed=False,
                denial_reason="Destructive keywords caught in tool parameters."
            )

        # 2. Force approval for broadcasting/social tools
        if request.action_name in self.broadcast_tools:
            return ToolRiskAssessment(
                risk_level="high",
                requires_approval=True,
                allowed=True,
                denial_reason=""
            )

        # 3. Default Safe Execution
        return ToolRiskAssessment(
            risk_level="low",
            requires_approval=False,
            allowed=True,
            denial_reason=""
        )
