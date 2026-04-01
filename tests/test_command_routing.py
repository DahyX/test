# -*- coding: utf-8 -*-
"""
test_command_routing.py — Command Routing Regression Tests
Verifies known commands route correctly, never hit generic fallback.
"""

import pytest
from unittest.mock import patch, MagicMock
from core.main_loop import AgentLoop
from reasoning.intent_analyzer import IntentAnalyzer
from core.change_history import ChangeHistoryStore
from core.routing_models import RequestScope, LocalStatusSummary

@pytest.fixture
def agent_loop():
    return AgentLoop()

@pytest.fixture
def mock_history_store():
    store = MagicMock(spec=ChangeHistoryStore)
    store.get_history_summary.return_value = "No local history found."
    summary = MagicMock(spec=LocalStatusSummary)
    summary.modified_files = []
    summary.successful_changes = 0
    summary.failed_changes = 0
    store.get_local_status_summary.return_value = summary
    return store

def test_patch_history_routes_correctly(agent_loop, mock_history_store):
    """patch history → LOCAL_HISTORY, not fallback."""
    with patch.object(agent_loop, 'history_store', mock_history_store):
        mock_history_store.get_history_summary.return_value = "Patch summary"
        result = agent_loop.run_cycle("patch history")
        assert "Patch summary" in result
        assert "Safe local chat fallback" not in result

def test_improvement_history_routes_correctly(agent_loop, mock_history_store):
    """improvement history → LOCAL_HISTORY."""
    with patch.object(agent_loop, 'history_store', mock_history_store):
        mock_history_store.get_history_summary.return_value = "Improvement summary"
        result = agent_loop.run_cycle("improvement history")
        assert "Improvement summary" in result

def test_benchmark_routes_to_handler_not_fallback(agent_loop):
    """benchmark → dedicated handler."""
    result = agent_loop.run_cycle("benchmark")
    assert "Benchmark support is coming" in result
    assert "Safe local chat fallback" not in result

def test_help_routes_to_handler_not_fallback(agent_loop):
    """help → dedicated handler."""
    result = agent_loop.run_cycle("help")
    assert "Supported commands:" in result
    assert "Safe local chat fallback" not in result

def test_benchmark_variants(agent_loop):
    """All benchmark patterns recognized."""
    for cmd in ["run benchmark", "benchmark status", "show benchmark"]:
        result = agent_loop.run_cycle(cmd)
        assert "Benchmark support" in result

def test_help_variants(agent_loop):
    """All help patterns recognized."""
    for cmd in ["what can you do", "show help", "commands"]:
        result = agent_loop.run_cycle(cmd)
        assert "Supported commands:" in result

def test_patch_history_empty_state(agent_loop, mock_history_store):
    """Empty history returns explicit message."""
    with patch.object(agent_loop, 'history_store', mock_history_store):
        mock_history_store.get_history_summary.return_value = "No local history found."
        result = agent_loop.run_cycle("show patches")
        assert "No local history found." in result

def test_generic_fallback_still_works_for_unmatched(agent_loop):
    """Truly unknown → fallback preserved."""
    result = agent_loop.run_cycle("talk about quantum physics")
    assert "Safe local chat fallback achieved." in result

def test_intent_analyzer_help_decision():
    """Analyzer produces correct decision."""
    analyzer = IntentAnalyzer()
    decision = analyzer.analyze_intent("help")
    assert decision.request_scope == RequestScope.HELP_REQUEST
    assert decision.confidence == 1.0

def test_intent_analyzer_benchmark_decision():
    """Analyzer produces correct decision."""
    analyzer = IntentAnalyzer()
    decision = analyzer.analyze_intent("benchmark status")
    assert decision.request_scope == RequestScope.BENCHMARK_REQUEST
