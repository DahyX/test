# -*- coding: utf-8 -*-
"""
llm_lab.py - LLM development roadmap support for Jarvis.

The plan is grounded in the public mlabonne/llm-course repository:
https://github.com/mlabonne/llm-course
"""

from __future__ import annotations

import re
from typing import Dict

from dataset_builder.jarvis_dataset_schema import build_example_from_exchange, write_jsonl


class LLMLabGuide:
    SOURCE_URL = "https://github.com/mlabonne/llm-course"

    def __init__(self, memory):
        self.memory = memory

    def matches(self, prompt: str) -> bool:
        lowered = (prompt or "").lower()
        return bool(
            re.search(
                r"(mlabonne|llm-course|build .* own llm|develop .* own llm|train .* llm|fine[- ]tune .* llm|jarvis .* llm|llm roadmap|llm export|export .*dataset)",
                lowered,
            )
        )

    def get_status(self) -> Dict[str, str]:
        state = self.memory.get_working_value(
            "llm_lab_state",
            {
                "phase": "curriculum",
                "focus": "Map Jarvis data, benchmarks, and fine-tuning tasks before training.",
            },
        )
        return {
            "phase": state.get("phase", "curriculum"),
            "focus": state.get("focus", ""),
            "source_url": self.SOURCE_URL,
            "dataset_path": state.get("dataset_path", ""),
            "dataset_examples": state.get("dataset_examples", 0),
        }

    def handle(self, prompt: str) -> str:
        lowered = (prompt or "").lower()
        if "export" in lowered and "dataset" in lowered:
            return self.export_sft_dataset()
        return self.build_plan()

    def build_plan(self) -> str:
        plan = {
            "phase": "dataset-and-sft",
            "focus": "Collect Jarvis conversations, repo QA traces, and benchmark prompts for supervised fine-tuning.",
        }
        self.memory.set_working("llm_lab_state", plan)

        return (
            "Jarvis LLM Lab roadmap based on mlabonne/llm-course:\n"
            f"Source: {self.SOURCE_URL}\n"
            "1. Fundamentals: use the course's math, Python, and neural-network foundations as the prerequisite layer.\n"
            "2. Scientist track for Jarvis: prepare a clean instruction dataset from Jarvis chats, repo-QA answers, self-check reports, and benchmark cases.\n"
            "3. Fine-tuning path: start with parameter-efficient supervised fine-tuning on a small open model using the course's QLoRA/Unsloth-style workflow, then iterate.\n"
            "4. Preference tuning: once SFT is stable, use ORPO or DPO-style alignment to improve helpfulness and reduce weak fallback behavior.\n"
            "5. Evaluation: mirror the course's AutoEval mindset by scoring Jarvis on chat quality, repo QA accuracy, benchmark pass rate, and self-check usefulness.\n"
            "6. Compression and deployment: use the course's quantization path to export compact models for local Jarvis use.\n"
            "7. Advanced evolution: explore merge and MoE workflows only after Jarvis has a reliable training dataset and evaluation loop.\n\n"
            "Immediate next step for this repo:\n"
            "- collect high-quality supervised examples from Jarvis interactions\n"
            "- keep a benchmark set of prompts and expected behaviors\n"
            "- fine-tune a small coding-friendly open model before attempting a full custom base model\n"
            "- treat 'build my own LLM' as a staged fine-tune/eval pipeline first, not a scratch-trained frontier model"
        )

    def export_sft_dataset(self, output_path: str = "training/jarvis_sft_dataset.jsonl") -> str:
        episodes = self.memory.get_recent_episodes(limit=400)
        examples = []
        pending_user = None

        for item in episodes:
            role = item.get("role")
            content = (item.get("content") or "").strip()
            if not content:
                continue

            if role == "user":
                pending_user = item
                continue

            if role == "assistant" and pending_user is not None:
                topic = pending_user.get("topic") or item.get("topic") or "general"
                related_memory = self.memory.build_chat_context(pending_user.get("content", ""), limit=2)
                examples.append(
                    build_example_from_exchange(
                        category="jarvis_runtime",
                        user_text=pending_user.get("content", "").strip(),
                        assistant_text=content,
                        topic=topic,
                        related_memory=[line for line in related_memory.splitlines() if line.strip()] or [f"topic:{topic}"],
                    )
                )
                pending_user = None

        write_jsonl(output_path, examples)

        state = {
            "phase": "dataset-exported",
            "focus": "Review the exported SFT dataset, curate weak examples, then start a small QLoRA-style fine-tune.",
            "dataset_path": output_path,
            "dataset_examples": len(examples),
        }
        self.memory.set_working("llm_lab_state", state)

        return (
            "Jarvis exported a starter supervised fine-tuning dataset.\n"
            f"Source course: {self.SOURCE_URL}\n"
            f"Output: {output_path}\n"
            f"Examples: {len(examples)}\n"
            "Format: JSONL Jarvis records with task, context, tools, plan, answer, verification, reflection, and messages.\n\n"
            "Recommended next steps:\n"
            "1. Remove weak fallback conversations and keep only strong grounded answers.\n"
            "2. Mix in benchmark prompts and expected outputs for evaluation.\n"
            "3. Fine-tune a small open instruct model with a QLoRA-style workflow before attempting larger experiments."
        )
