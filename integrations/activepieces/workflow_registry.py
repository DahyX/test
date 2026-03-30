# -*- coding: utf-8 -*-
"""
workflow_registry.py — Permitted Workflows
Provides explicit allowlisting for which 3rd-party SaaS workflows Jarvis is legally allowed to invoke.
"""

from typing import Dict, Optional
from tools.activepieces_models import ActivepiecesWorkflowDescriptor

class WorkflowRegistry:
    def __init__(self):
        # Strict hardcoded dict to prevent hallucinated workflow IDs
        self._registry: Dict[str, ActivepiecesWorkflowDescriptor] = {
            "slack_post": ActivepiecesWorkflowDescriptor(
                workflow_id="wf_slack_xyz123",
                name="Slack Post",
                description="Posts a message to the general Slack channel.",
                expected_parameters=["text_content"]
            ),
            "email_summary": ActivepiecesWorkflowDescriptor(
                workflow_id="wf_mail_abc456",
                name="Email Summary",
                description="Emails a summary to a designated address.",
                expected_parameters=["subject", "body", "recipient"]
            )
        }

    def get_workflow(self, semantic_intent: str) -> Optional[ActivepiecesWorkflowDescriptor]:
        """Maps a requested intent action safely against the explicit allowlist."""
        # TODO: Move to a vector lookup if registry grows, but enforce strict boundaries
        if "slack" in semantic_intent.lower():
            return self._registry.get("slack_post")
        if "email" in semantic_intent.lower():
            return self._registry.get("email_summary")
        return None

    def is_valid(self, workflow_id: str) -> bool:
        """Confirms workflow ID actually exists before routing."""
        return any(w.workflow_id == workflow_id for w in self._registry.values())
