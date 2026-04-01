# -*- coding: utf-8 -*-
"""
Regression coverage for repo QA, offline memory, and the LLM lab guide.
"""

import json

from core.main_loop import AgentLoop
from core.llm_lab import LLMLabGuide
from core.offline_memory import OfflineMemory


def test_repo_question_answers_from_local_code():
    loop = AgentLoop()
    result = loop.run_cycle("explain core/main_loop.py")

    assert "Repo answer based on local code:" in result
    assert "Best match: core/main_loop.py" in result


def test_llm_lab_plan_is_grounded_in_course_repo():
    loop = AgentLoop()
    result = loop.run_cycle("use mlabonne llm-course to help jarvis build his own llm")

    assert "https://github.com/mlabonne/llm-course" in result
    assert "QLoRA" in result or "parameter-efficient" in result


def test_offline_memory_persists_and_searches(tmp_path):
    db_path = tmp_path / "memory.db"
    memory = OfflineMemory(db_path=str(db_path), session_id="test")
    memory.remember_exchange(
        "explain the plugin loader",
        "The plugin loader scans the plugins folder and dispatches actions.",
        topic="plugin loader",
    )

    hits = memory.search_episodes("plugin loader", limit=5)
    recent = memory.get_recent_episodes(limit=5)

    assert len(recent) == 2
    assert hits
    assert any("plugin loader" in item["content"].lower() for item in hits + recent)


def test_llm_lab_can_export_sft_dataset(tmp_path):
    db_path = tmp_path / "memory.db"
    output_path = tmp_path / "training" / "jarvis_sft_dataset.jsonl"
    memory = OfflineMemory(db_path=str(db_path), session_id="lab")
    memory.remember_exchange(
        "explain the plugin loader",
        "The plugin loader scans the plugins folder and dispatches actions.",
        topic="plugin loader",
    )

    guide = LLMLabGuide(memory)
    result = guide.export_sft_dataset(str(output_path))

    assert output_path.exists()
    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["input_task"] == "explain the plugin loader"
    assert record["messages"][1]["role"] == "user"
    assert record["messages"][2]["role"] == "assistant"
    assert "Examples: 1" in result
