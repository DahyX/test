# -*- coding: utf-8 -*-
"""
test_jarvis_stabilization.py — Integration Regression Coverage
Asserts explicitly safe behaviors enforce all bounds correctly.
"""

import pytest
from core.routing_models import RequestScope
from core.source_permissions import get_routing_decision
from reasoning.intent_analyzer import IntentAnalyzer
from core.main_loop import AgentLoop
from self_improvement.patch_proposer import PatchProposer
from self_improvement.patch_evaluator import PatchEvaluator

def test_local_status_no_web():
    decision = get_routing_decision(RequestScope.LOCAL_STATUS)
    assert "web_search" in decision.forbidden_sources
    assert decision.requires_web is False

def test_intent_analyzer_local_status():
    analyzer = IntentAnalyzer()
    decision = analyzer.analyze_intent("did you work on any files until now?")
    assert decision.request_scope == RequestScope.LOCAL_STATUS
    assert "web_search" in decision.forbidden_sources

def test_patch_proposer_requires_target():
    proposer = PatchProposer()
    result = proposer.propose_patch("improve everything", "")
    assert "error" in result
    assert "Missing explicit target file" in result["error"]

def test_patch_evaluator_no_auto_apply():
    evaluator = PatchEvaluator(sandbox_mode=False)
    result = evaluator.evaluate_and_apply({"target": "core/main_loop.py"}, manual_approval=False)
    assert result["status"] == "blocked"

def test_main_loop_local_status_fallback(mocker):
    loop = AgentLoop()
    mocker.patch.object(loop.history_store, "get_local_status_summary")
    loop.run_cycle("did you work on any files?")
    loop.history_store.get_local_status_summary.assert_called_once()
