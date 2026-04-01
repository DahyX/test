# -*- coding: utf-8 -*-
"""
test_command_routing.py - Command routing regression tests.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.change_history import ChangeHistoryStore
from core.main_loop import AgentLoop
from core.routing_models import LocalStatusSummary, RequestScope
from reasoning.intent_analyzer import IntentAnalyzer


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
    summary.recent_attempts = []
    store.get_local_status_summary.return_value = summary
    return store


def test_patch_history_routes_correctly(agent_loop, mock_history_store):
    with patch.object(agent_loop, "history_store", mock_history_store):
        mock_history_store.get_history_summary.return_value = "Patch summary"
        result = agent_loop.run_cycle("patch history")
    assert "Patch summary" in result


def test_improvement_history_routes_correctly(agent_loop, mock_history_store):
    with patch.object(agent_loop, "history_store", mock_history_store):
        mock_history_store.get_history_summary.return_value = "Improvement summary"
        result = agent_loop.run_cycle("improvement history")
    assert "Improvement summary" in result


def test_benchmark_routes_to_handler(agent_loop):
    result = agent_loop.run_cycle("benchmark")
    assert "Benchmark Results:" in result


def test_help_routes_to_handler(agent_loop):
    result = agent_loop.run_cycle("help")
    assert "Supported commands:" in result


def test_benchmark_variants(agent_loop):
    for cmd in ["run benchmark", "benchmark status", "show benchmark"]:
        result = agent_loop.run_cycle(cmd)
        assert "Benchmark Results:" in result


def test_help_variants(agent_loop):
    for cmd in ["what can you do", "show help", "commands"]:
        result = agent_loop.run_cycle(cmd)
        assert "Supported commands:" in result


def test_patch_history_empty_state(agent_loop, mock_history_store):
    with patch.object(agent_loop, "history_store", mock_history_store):
        mock_history_store.get_history_summary.return_value = "No local history found."
        result = agent_loop.run_cycle("show patches")
    assert "No local history found." in result


def test_generic_chat_fallback_is_helpful_when_no_backend(agent_loop):
    with patch.object(agent_loop, "_chat_with_model", return_value=None):
        result = agent_loop.run_cycle("talk about quantum physics")
    assert "I couldn't reach a conversational model backend" in result


def test_self_check_routes_to_dedicated_handler(agent_loop):
    result = agent_loop.run_cycle("self-check")
    assert "Self-check summary:" in result


def test_intent_analyzer_help_decision():
    analyzer = IntentAnalyzer()
    decision = analyzer.analyze_intent("help")
    assert decision.request_scope == RequestScope.HELP_REQUEST
    assert decision.confidence == 1.0


def test_intent_analyzer_benchmark_decision():
    analyzer = IntentAnalyzer()
    decision = analyzer.analyze_intent("benchmark status")
    assert decision.request_scope == RequestScope.BENCHMARK_REQUEST


def test_intent_analyzer_self_check_decision():
    analyzer = IntentAnalyzer()
    decision = analyzer.analyze_intent("self-check")
    assert decision.request_scope == RequestScope.SELF_CHECK_REQUEST
