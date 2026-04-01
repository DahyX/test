"""
jarvis_dataset_schema.py - Dataset schema helpers for Jarvis training data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from typing import Any, Dict, Iterable, List


JARVIS_DATASET_FILES = [
    "jarvis_identity.jsonl",
    "jarvis_reasoning.jsonl",
    "jarvis_coding.jsonl",
    "jarvis_tooluse.jsonl",
    "jarvis_memory.jsonl",
    "jarvis_selfcheck.jsonl",
    "jarvis_self_improvement.jsonl",
    "jarvis_reflection.jsonl",
]


@dataclass
class JarvisDatasetExample:
    category: str
    input_task: str
    context: Dict[str, Any]
    available_tools: List[str]
    relevant_memory: List[str]
    expected_plan: List[str]
    expected_answer: str
    expected_tool_usage: List[str]
    expected_verification: List[str]
    expected_reflection: str
    outcome_notes: str
    messages: List[Dict[str, str]] = field(default_factory=list)

    def validate(self) -> None:
        required_text = {
            "category": self.category,
            "input_task": self.input_task,
            "expected_answer": self.expected_answer,
            "expected_reflection": self.expected_reflection,
            "outcome_notes": self.outcome_notes,
        }
        for field_name, value in required_text.items():
            if not str(value).strip():
                raise ValueError(f"Missing required field: {field_name}")

        required_lists = {
            "available_tools": self.available_tools,
            "expected_plan": self.expected_plan,
            "expected_tool_usage": self.expected_tool_usage,
            "expected_verification": self.expected_verification,
        }
        for field_name, value in required_lists.items():
            if not value:
                raise ValueError(f"Missing required list field: {field_name}")

    def to_record(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)


def build_example_from_exchange(
    category: str,
    user_text: str,
    assistant_text: str,
    topic: str = "general",
    available_tools: List[str] = None,
    related_memory: List[str] = None,
) -> JarvisDatasetExample:
    tools = available_tools or ["offline_memory", "repo_qa", "self_check", "claude_inheritance"]
    memory = related_memory or [f"topic:{topic}"]
    plan = [
        "Interpret the request and classify the task.",
        "Retrieve relevant repo or memory context before answering.",
        "Answer concretely and stay grounded in local evidence.",
    ]
    verification = [
        "Check whether the answer is grounded in repo context or known memory.",
        "If code changes are proposed, require tests or a verifier pass before adoption.",
    ]
    reflection = (
        "Store the interaction if it was useful, and mark weak fallback behavior for later curation."
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are Jarvis, a grounded engineering intelligence that plans, verifies, and learns carefully."
            ),
        },
        {"role": "user", "content": user_text.strip()},
        {"role": "assistant", "content": assistant_text.strip()},
    ]
    return JarvisDatasetExample(
        category=category,
        input_task=user_text.strip(),
        context={"topic": topic, "source": "jarvis_offline_memory"},
        available_tools=tools,
        relevant_memory=memory,
        expected_plan=plan,
        expected_answer=assistant_text.strip(),
        expected_tool_usage=["memory lookup", "repo grounding when relevant"],
        expected_verification=verification,
        expected_reflection=reflection,
        outcome_notes="Starter record exported from Jarvis runtime memory for later curation.",
        messages=messages,
    )


def write_jsonl(path: str, examples: Iterable[JarvisDatasetExample]) -> int:
    records = [example.to_record() for example in examples]
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=True) + "\n")
    return len(records)
