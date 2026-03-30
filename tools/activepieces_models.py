# -*- coding: utf-8 -*-
"""
activepieces_models.py — Data Contracts for Backend Delegation
Defines strictly typed structs handling the exchange of tool parameters between Jarvis and Activepieces.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class ToolExecutionRequest:
    tool_name: str
    action_name: str
    parameters: Dict[str, Any]
    user_intent: str
    request_scope: str
    requires_approval: bool = False
    risk_level: str = "low"
    trace_id: str = "trace-0000"

@dataclass
class ToolExecutionResult:
    success: bool
    tool_name: str
    action_name: str
    raw_result: str
    normalized_result: str = ""
    error_message: str = ""
    execution_time_ms: int = 0

@dataclass
class WorkflowInvocation:
    workflow_id: str
    workflow_name: str
    input_payload: Dict[str, Any]
    requires_approval: bool = True
    approval_context: str = "Pending manual confirmation"
    requested_by: str = "jarvis_core"
    trace_id: str = "trace-0000"

@dataclass
class WorkflowStepResult:
    step_id: str
    output: Any
    success: bool

@dataclass
class ApprovalRequirement:
    required: bool
    reason: str
    risk_level: str
    confirmation_message: str

@dataclass
class ApprovalDecision:
    approved: bool
    user: str
    timestamp: str
    overrides: Optional[Dict[str, Any]] = None

@dataclass
class ActivepiecesActionDescriptor:
    action_type: str
    capabilities: list
    safe_to_automate: bool

@dataclass
class ActivepiecesWorkflowDescriptor:
    workflow_id: str
    name: str
    description: str
    expected_parameters: list

@dataclass
class ToolRiskAssessment:
    risk_level: str
    requires_approval: bool
    allowed: bool
    denial_reason: str = ""

@dataclass
class WorkflowExecutionSummary:
    workflow_id: str
    status: str
    steps_completed: int
    final_output: str
