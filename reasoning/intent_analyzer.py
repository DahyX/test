# -*- coding: utf-8 -*-
"""
intent_analyzer.py — Deterministic Gatekeeper
Overrides the loose V5/V6 LLM intent guessers. Uses hard heuristics first to map exactly
into a `RequestRoutingDecision`.
"""

from typing import Optional
from core.routing_models import RequestRoutingDecision
from core.source_permissions import SourcePermissionsPolicy

class IntentAnalyzer:
    def __init__(self):
        self.policy = SourcePermissionsPolicy()
        
        # Rigid Heuristics to block hallucinations
        self.local_status_triggers = ["did you work on", "did you edit", "what did you change", "status", "recent files"]
        self.history_triggers = ["improvement history", "patch history", "previous attempts"]
        self.web_triggers = ["google", "search the web", "look up"]
        self.improvement_triggers = ["optimize", "refactor", "upgrade", "patch"]

    def evaluate(self, user_input: str) -> RequestRoutingDecision:
        """Determines routing scope systematically. LLM fallback ONLY if all fail."""
        text = user_input.lower()
        scope = "chat"
        reason = "Fallback to generic chat."

        # 1. Hardware-level interception of local questions
        if any(t in text for t in self.local_status_triggers):
            scope = "local_status"
            reason = "Keyword matched local file status query."
        elif any(t in text for t in self.history_triggers):
            scope = "local_history"
            reason = "Keyword matched improvement history log query."
        elif any(t in text for t in self.improvement_triggers):
            scope = "self_improvement_request"
            reason = "Keyword matched codebase patching."
        elif any(t in text for t in self.web_triggers):
            scope = "web_research"
            reason = "Keyword explicitly requested internet."
        
        # Assume LLM fallback for repository logic if code indicators are present
        elif "code" in text or "function" in text or "file" in text:
            scope = "repo_code_question"
            reason = "Heuristic code question."

        # Bind permission matrix
        perms = self.policy.get_policy(scope)
        decision = RequestRoutingDecision(
            request_scope=scope,
            allowed_sources=perms["allowed_sources"],
            forbidden_sources=perms["forbidden_sources"],
            requires_web=perms["requires_web"],
            requires_local_state=perms["requires_local_state"],
            requires_tools=perms["requires_tools"],
            reason=reason
        )
        return decision
