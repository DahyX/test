# -*- coding: utf-8 -*-
"""
routing_models.py — Strict Routing Contracts
Defines the safe data bounds for intercepting user requests before tool execution.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List

class RequestScope(str, Enum):
    LOCAL_STATUS = "local_status"
    LOCAL_HISTORY = "local_history"
    BENCHMARK_REQUEST = "benchmark_request"
    HELP_REQUEST = "help_request"
    CHAT = "chat"
    REPO_CODE_QUESTION = "repo_code_question"
    WEB_RESEARCH = "web_research"
    DESKTOP_ACTION = "desktop_action"
    SELF_IMPROVEMENT_REQUEST = "self_improvement_request"

@dataclass
class RequestRoutingDecision:
    request_scope: RequestScope = RequestScope.CHAT
    allowed_sources: List[str] = field(default_factory=list)
    forbidden_sources: List[str] = field(default_factory=lambda: ["web_search", "external_retrieval"])
    requires_web: bool = False
    requires_local_state: bool = False
    requires_tools: bool = False
    reason: str = "Default safe chat routing."
    confidence: float = 1.0

@dataclass
class ChangeRecord:
    timestamp: str
    action_type: str
    target_file: str
    status: str
    reason: str
    session_id: str = "local_session"

@dataclass
class ImprovementRecord:
    timestamp: str
    candidate_name: str
    target: str
    status: str
    result_summary: str
    session_id: str = "local_session"

@dataclass
class LocalStatusSummary:
    modified_files: List[str] = field(default_factory=list)
    successful_changes: int = 0
    failed_changes: int = 0
    recent_attempts: List[str] = field(default_factory=list)
