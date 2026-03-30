# -*- coding: utf-8 -*-
"""
test_activepieces_integration.py — Pytest suite for strict execution boundaries.
"""

import pytest
from tools.activepieces_models import ToolExecutionRequest, WorkflowInvocation
from integrations.activepieces.workflow_registry import WorkflowRegistry
from tools.activepieces_mapper import ActivepiecesMapper
from tools.activepieces_bridge import ActivepiecesBridge
from safety.action_guard import ActionGuard
from safety.tool_risk_policy import ToolRiskPolicy

def test_workflow_registry_blocks_unknown():
    registry = WorkflowRegistry()
    assert registry.is_valid("wf_slack_xyz123") is True
    assert registry.is_valid("wf_hack_bank_999") is False
    assert registry.get_workflow("do a random hack") is None

def test_mapper_translates_correctly():
    mapper = ActivepiecesMapper()
    req = ToolExecutionRequest(
        tool_name="activepieces",
        action_name="slack_post",
        parameters={"text_content": "Hello team!"},
        user_intent="Tell the team I am done logging off",
        request_scope="chat"
    )
    invocation = mapper.translate_request(req)
    assert invocation is not None
    assert invocation.workflow_id == "wf_slack_xyz123"
    assert invocation.input_payload["text_content"] == "Hello team!"

def test_action_guard_blocks_local_status():
    guard = ActionGuard()
    req = ToolExecutionRequest(
        tool_name="activepieces",
        action_name="slack_post",
        parameters={},
        user_intent="Check files",
        request_scope="local_status"
    )
    # Never allow external actions when scope is local status
    assert guard.is_execution_safely_permitted(req) is False

def test_bridge_rejects_unapproved_invocations():
    bridge = ActivepiecesBridge()
    inv = WorkflowInvocation(
        workflow_id="wf_email",
        workflow_name="email",
        input_payload={},
        requires_approval=True,  # Approval was NOT resolved by ApprovalAdapter
        approval_context="Mocking an unapproved request"
    )
    result = bridge.execute(inv)
    assert result.success is False
    assert "Approval flag was still active" in result.error_message

def test_tool_risk_policy_catches_broadcasts():
    policy = ToolRiskPolicy()
    req = ToolExecutionRequest(
        tool_name="activepieces",
        action_name="slack_post",
        parameters={"text": "Hello"},
        user_intent="Update slack",
        request_scope="chat"
    )
    assessment = policy.assess(req)
    assert assessment.requires_approval is True
    assert assessment.risk_level == "high"
