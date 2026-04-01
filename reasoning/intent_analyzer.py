# -*- coding: utf-8 -*-
"""
intent_analyzer.py — Deterministic Intent Resolution
Defines heuristic checks to avoid ambiguous broad evaluation on meta prompts.
"""

import re
from core.routing_models import RequestScope, RequestRoutingDecision
from core.source_permissions import get_routing_decision

class IntentAnalyzer:
    """Analyzes intent deterministically before calling broad retrieval."""
    
    LOCAL_STATUS_REGEX = re.compile(r"(did you work on any files|what did you change|did you edit anything|^status$)", re.IGNORECASE)
    LOCAL_HISTORY_REGEX = re.compile(r"(improvement history|show (?:previous )?(?:patch|improvement) (?:history|attempts?)|show patches|recent patches|patch history)", re.IGNORECASE)
    BENCHMARK_REGEX = re.compile(r"(benchmark|run benchmark|benchmark status|show benchmark)", re.IGNORECASE)
    HELP_REGEX = re.compile(r"(help|what can you do|commands|show help|available commands)", re.IGNORECASE)
    SELF_CHECK_REGEX = re.compile(r"^(self-check|self check|health check|system health)$", re.IGNORECASE)
    REPO_CODE_REGEX = re.compile(r"(inspect local code|show me the code|what is in\s+\w+\.py)", re.IGNORECASE)
    SELF_IMPROVEMENT_REGEX = re.compile(r"(improve yourself|patch yourself|modify your codebase)", re.IGNORECASE)
    
    def analyze_intent(self, prompt: str) -> RequestRoutingDecision:
        """Deterministically classifies request to hard behavior bounds."""
        
        if self.HELP_REGEX.search(prompt):
            return RequestRoutingDecision(
                request_scope=RequestScope.HELP_REQUEST,
                reason="Matched help command heuristics.",
                confidence=1.0
            )
            
        if self.BENCHMARK_REGEX.search(prompt):
            return RequestRoutingDecision(
                request_scope=RequestScope.BENCHMARK_REQUEST,
                reason="Matched benchmark command heuristics.",
                confidence=1.0
            )

        if self.SELF_CHECK_REGEX.search(prompt):
            return get_routing_decision(RequestScope.SELF_CHECK_REQUEST, reason="Matched self-check heuristics.")
            
        if self.LOCAL_STATUS_REGEX.search(prompt):
            return get_routing_decision(RequestScope.LOCAL_STATUS, reason="Matched local status heuristics.")
            
        if self.LOCAL_HISTORY_REGEX.search(prompt):
            return get_routing_decision(RequestScope.LOCAL_HISTORY, reason="Matched local history heuristics.")
            
        if self.SELF_IMPROVEMENT_REGEX.search(prompt):
            return get_routing_decision(RequestScope.SELF_IMPROVEMENT_REQUEST, reason="Matched self-improvement heuristics.")
            
        if self.REPO_CODE_REGEX.search(prompt):
            return get_routing_decision(RequestScope.REPO_CODE_QUESTION, reason="Matched repository code heuristics.")
            
        return get_routing_decision(RequestScope.CHAT, reason="Fallback to safe chat defaults.")
