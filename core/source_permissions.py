# -*- coding: utf-8 -*-
"""
source_permissions.py — Source Use Policies
Implements explicit source permission rules mapped from RequestScope.
"""

from core.routing_models import RequestScope, RequestRoutingDecision

def get_routing_decision(scope: RequestScope, reason: str = "") -> RequestRoutingDecision:
    """Returns a secure routing decision based on the scope."""
    base_decision = RequestRoutingDecision(
        request_scope=scope,
        reason=reason,
        confidence=1.0,
        forbidden_sources=["web_search", "external_retrieval", "broad_semantic_search"]
    )
    
    if scope in (RequestScope.LOCAL_STATUS, RequestScope.LOCAL_HISTORY):
        # Explicit deny for web and broad search
        base_decision.requires_local_state = True
        return base_decision

    elif scope == RequestScope.REPO_CODE_QUESTION:
        base_decision.allowed_sources = ["local_workspace"]
        base_decision.requires_local_state = True
        return base_decision

    elif scope == RequestScope.WEB_RESEARCH:
        base_decision.allowed_sources = ["web_search", "external_retrieval"]
        base_decision.forbidden_sources = []
        base_decision.requires_web = True
        return base_decision

    elif scope == RequestScope.DESKTOP_ACTION:
        base_decision.allowed_sources = ["desktop_tools"]
        base_decision.requires_tools = True
        return base_decision

    elif scope == RequestScope.SELF_IMPROVEMENT_REQUEST:
        base_decision.allowed_sources = ["local_workspace"]
        base_decision.requires_local_state = True
        base_decision.requires_tools = True
        return base_decision

    else:
        # CHAT or UNKNOWN defaults to strict safety
        return base_decision
