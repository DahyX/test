# -*- coding: utf-8 -*-
"""
approval_adapter.py — Human In The Loop Gateway
Mocks pausing backend execution until human permission is granted for high-risk executions.
"""

from tools.activepieces_models import WorkflowInvocation, ApprovalDecision
import datetime

class ApprovalAdapter:
    def __init__(self):
        self.auto_reject_timeout = 300 # seconds

    def request_approval(self, invocation: WorkflowInvocation) -> ApprovalDecision:
        """
        Pauses the loop to request manual review.
        """
        # TODO: Hook to frontend GUI/WebSocket or CLI blocking prompt
        # Safe Placeholder: Deny auto-approve by default. Simulate terminal block.
        
        print("\n" + "="*50)
        print(f"⚠️  APPROVAL REQUIRED: Workflow [{invocation.workflow_name}]")
        print(f"Payload: {invocation.input_payload}")
        print("="*50 + "\n")
        
        return ApprovalDecision(
            approved=False,
            user="system_timeout",
            timestamp=datetime.datetime.now().isoformat(),
            overrides=None
        )
