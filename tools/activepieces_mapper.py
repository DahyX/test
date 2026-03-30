# -*- coding: utf-8 -*-
"""
activepieces_mapper.py — Grammar Translation
Converts Jarvis's abstract semantic intention into structured JSON payloads satisfying Activepieces schemas.
"""

from typing import Dict, Any, Optional
from tools.activepieces_models import WorkflowInvocation, ToolExecutionRequest
from integrations.activepieces.workflow_registry import WorkflowRegistry

class ActivepiecesMapper:
    def __init__(self):
        self.registry = WorkflowRegistry()

    def translate_request(self, request: ToolExecutionRequest) -> Optional[WorkflowInvocation]:
        """
        Maps a generic semantic intent (e.g. 'tell my team I am deploying') into an explicit API Invoke target.
        """
        workflow_desc = self.registry.get_workflow(request.action_name)
        
        if not workflow_desc:
            return None
            
        # TODO: Dynamically align parameters using LLM or fixed mapping matrix
        # Placeholder naive mapping assuming Jarvis reasoning already standardized output keys
        payload = request.parameters
        
        invocation = WorkflowInvocation(
            workflow_id=workflow_desc.workflow_id,
            workflow_name=workflow_desc.name,
            input_payload=payload,
            requires_approval=request.requires_approval,
            approval_context=f"Jarvis intends to use {workflow_desc.name} due to '{request.user_intent}'",
            requested_by="jarvis_core",
            trace_id=request.trace_id
        )
        
        return invocation
