# -*- coding: utf-8 -*-
"""
Regression coverage for the live Claude inheritance path.
"""

from unittest.mock import patch

from core.main_loop import AgentLoop
from web_server import JarvisWrapper


def test_claude_status_reports_both_bundled_repos():
    loop = AgentLoop()
    result = loop.run_cycle("claude status")

    assert "Claude inheritance is active in Jarvis." in result
    assert "everything-claude-code-main" in result
    assert "Claude-Code-Extended-Source-main" in result


def test_plan_slash_command_routes_into_inherited_ecc_command():
    loop = AgentLoop()

    with patch.object(loop.plugin_loader, "handle", return_value="planned") as mocked_handle:
        result = loop.run_cycle("/plan improve jarvis")

    assert result == "planned"
    mocked_handle.assert_called_once()
    assert mocked_handle.call_args[0][0] == "ecc_cmd_plan"
    assert mocked_handle.call_args[0][1]["query"] == "improve jarvis"


def test_review_alias_routes_into_inherited_cce_command_alias():
    loop = AgentLoop()

    with patch.object(loop.plugin_loader, "handle", return_value="reviewed") as mocked_handle:
        result = loop.run_cycle("/review auth changes")

    assert result == "reviewed"
    mocked_handle.assert_called_once()
    assert mocked_handle.call_args[0][0] == "cce_cmd_review"
    assert mocked_handle.call_args[0][1]["query"] == "auth changes"


def test_architect_agent_routes_into_inherited_agent():
    loop = AgentLoop()

    with patch.object(loop.plugin_loader, "handle", return_value="architecture ready") as mocked_handle:
        result = loop.run_cycle("@architect redesign the runtime bridge")

    assert result == "architecture ready"
    mocked_handle.assert_called_once()
    assert mocked_handle.call_args[0][0] == "ecc_agent_architect"
    assert mocked_handle.call_args[0][1]["query"] == "redesign the runtime bridge"


def test_web_wrapper_exposes_inherited_runtime_counts():
    wrapper = JarvisWrapper()
    stats = wrapper.memory.stats()

    assert wrapper.brain.model == "Jarvis V6 + Claude Inheritance"
    assert stats["episodes"] >= 0
    assert wrapper.runtime_status["ecc_command_count"] > 0
    assert wrapper.runtime_status["ecc_agent_count"] > 0
