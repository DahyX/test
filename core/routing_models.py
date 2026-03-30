# -*- coding: utf-8 -*-
"""
routing_models.py — Strict Routing Contracts
Defines the safe data bounds for intercepting user requests before tool execution.
"""

from dataclasses import dataclass, field
from typing import List

@dataclass
class RequestRoutingDecision:
    request_scope: str = "chat"
    allowed_sources: List[str] = field(default_factory=list)
    forbidden_sources: List[str] = field(default_factory=lambda: ["web_search", "external_retrieval"])
    requires_web: bool = False
    requires_local_state: bool = False
    requires_tools: bool = False
    reason: str = "Default safe chat routing."

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

@dataclass
class LocalStatusSummary:
    modified_files: List[str] = field(default_factory=list)
    successful_changes: int = 0
    failed_changes: int = 0
    recent_attempts: List[str] = field(default_factory=list)
