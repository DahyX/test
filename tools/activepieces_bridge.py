# -*- coding: utf-8 -*-
"""
activepieces_bridge.py — Primary Execution Gateway
Accepts authorized workflow invocations, triggers the client, and returns a raw result.
"""

from tools.activepieces_models import WorkflowInvocation, ToolExecutionResult
from tools.activepieces_client import ActivepiecesClient
from integrations.activepieces.config import load_config

class ActivepiecesBridge:
    def __init__(self):
        self.config = load_config()
        self.client = ActivepiecesClient(self.config)

    def execute(self, invocation: WorkflowInvocation) -> ToolExecutionResult:
        """Fires the mapped payload to the client and wraps the raw return."""
        
        # Hard fail if requires_approval is inappropriately set 
        # (This should have been cleared by the ApprovalAdapter before reaching the bridge)
        if invocation.requires_approval:
             return ToolExecutionResult(
                 success=False,
                 tool_name="activepieces_bridge",
                 action_name=invocation.workflow_name,
                 raw_result="",
                 error_message="Bridge received unauthorized invocation. Approval flag was still active."
             )
        
        success, raw_output, err = self.client.execute_workflow(invocation.workflow_id, invocation.input_payload)
        
        return ToolExecutionResult(
            success=success,
            tool_name="activepieces",
            action_name=invocation.workflow_name,
            raw_result=str(raw_output) if success else "",
            error_message=err
        )
