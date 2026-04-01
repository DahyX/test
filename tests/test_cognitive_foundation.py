# -*- coding: utf-8 -*-
"""
Regression coverage for the next-generation Jarvis foundation modules.
"""

import json
import os

from cognition.foundation import NextGenerationFoundation
from core.main_loop import AgentLoop
from dataset_builder.jarvis_dataset_schema import build_example_from_exchange, write_jsonl


def test_foundation_status_defines_stack_and_autonomy():
    foundation = NextGenerationFoundation(project_root=os.getcwd())
    status = foundation.get_status()

    assert status["model_roles"] >= 5
    assert status["verifier_stages"] >= 5
    assert status["autonomy_jobs"] >= 4
    assert status["dataset_files_expected"] == 8


def test_dataset_schema_writes_valid_record(tmp_path):
    output_path = tmp_path / "sample.jsonl"
    example = build_example_from_exchange(
        category="jarvis_runtime",
        user_text="explain the plugin loader",
        assistant_text="The plugin loader scans the plugins folder and dispatches actions.",
        topic="plugin loader",
    )

    count = write_jsonl(str(output_path), [example])

    assert count == 1
    record = json.loads(output_path.read_text(encoding="utf-8").strip())
    assert record["input_task"] == "explain the plugin loader"
    assert record["expected_plan"]
    assert record["messages"][1]["role"] == "user"


def test_loop_exposes_cognitive_status():
    loop = AgentLoop()
    result = loop.run_cycle("cognitive status")

    assert "Jarvis cognitive foundation:" in result
    assert "jarvis-general" in result
    assert "Autonomy jobs:" in result
