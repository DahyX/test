# -*- coding: utf-8 -*-
"""
test_routing_safety.py — Pytest suite verifying the Emergency Repair routing integrity.
"""

import pytest
from core.routing_models import RequestRoutingDecision
from reasoning.intent_analyzer import IntentAnalyzer
from core.change_history import ChangeHistoryStore
from core.main_loop import AgentLoop
from self_improvement.patch_proposer import PatchProposer
from self_improvement.patch_evaluator import PatchEvaluator

def test_local_status_denies_web():
    analyzer = IntentAnalyzer()
    decision = analyzer.evaluate("did you work on any files until now?")
    
    assert decision.request_scope == "local_status"
    assert "web_search" in decision.forbidden_sources
    assert decision.requires_web is False
    assert decision.requires_local_state is True

def test_improvement_history_uses_local_history():
    analyzer = IntentAnalyzer()
    decision = analyzer.evaluate("show me your improvement history")
    
    assert decision.request_scope == "local_history"
    assert "web_search" in decision.forbidden_sources
    assert decision.requires_local_state is True

def test_missing_target_aborts_patch():
    proposer = PatchProposer()
    proposal = proposer.propose_patch("make the reasoning logic faster")
    
    assert proposal["success"] is False
    assert "Explicit target file required" in proposal["error"]

def test_patch_evaluator_blocks_auto_apply():
    evaluator = PatchEvaluator()
    proposal = {"success": True, "target_file": "core/main_loop.py"}
    
    # Passing sandbox_mode=False and manual_approval=False to trigger the hard block
    result = evaluator.evaluate_and_apply(proposal, manual_approval=False, sandbox_mode=False)
    
    assert "Auto-apply is globally disabled" in result

def test_unknown_local_status_answers_plainly():
    loop = AgentLoop()
    # Assuming fresh loop has empty history
    result = loop.step("did you work on any files?")
    
    assert "No recorded file modifications" in result
    
def test_request_scope_classification_works():
    analyzer = IntentAnalyzer()
    decision_chat = analyzer.evaluate("hello world")
    assert decision_chat.request_scope == "chat"
    
    decision_web = analyzer.evaluate("google the current weather")
    assert decision_web.request_scope == "web_research"
    assert decision_web.requires_web is True

def test_source_permission_enforcement_works():
    loop = AgentLoop()
    # This shouldn't reach web tool because history handles it, but if it did, it's blocked.
    decision = loop.intent.evaluate("did you edit anything")
    assert "web_search" in decision.forbidden_sources
