"""
jarvis_model_stack.py - Explicit multi-role model strategy for Jarvis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ModelRoleSpec:
    name: str
    purpose: str
    responsibilities: List[str] = field(default_factory=list)
    preferred_backends: List[str] = field(default_factory=list)
    verifier_required: bool = False


class JarvisModelStack:
    def __init__(self):
        self.roles: Dict[str, ModelRoleSpec] = {
            "jarvis-general": ModelRoleSpec(
                name="jarvis-general",
                purpose="Primary assistant responses with memory awareness and grounded execution hints.",
                responsibilities=["chat", "status", "light planning"],
                preferred_backends=["qwen", "llama", "ollama"],
            ),
            "jarvis-coder": ModelRoleSpec(
                name="jarvis-coder",
                purpose="Repo inspection, patch generation, debugging, and safe refactors.",
                responsibilities=["coding", "patching", "test-aware fixes"],
                preferred_backends=["qwen", "deepseek", "ollama"],
                verifier_required=True,
            ),
            "jarvis-reasoner": ModelRoleSpec(
                name="jarvis-reasoner",
                purpose="Multi-step diagnosis, architecture work, decomposition, and tradeoff analysis.",
                responsibilities=["reasoning", "planning", "diagnostics"],
                preferred_backends=["deepseek", "qwen", "ollama"],
            ),
            "jarvis-verifier": ModelRoleSpec(
                name="jarvis-verifier",
                purpose="Check outputs, benchmark deltas, safety risks, and regression exposure.",
                responsibilities=["verification", "benchmark review", "consistency checks"],
                preferred_backends=["qwen", "llama", "ollama"],
                verifier_required=True,
            ),
            "jarvis-memory-router": ModelRoleSpec(
                name="jarvis-memory-router",
                purpose="Retrieve and rank episodic, semantic, procedural, and project memory.",
                responsibilities=["retrieval", "memory ranking", "context shaping"],
                preferred_backends=["local-heuristics", "qwen"],
            ),
            "jarvis-trainer": ModelRoleSpec(
                name="jarvis-trainer",
                purpose="Curate datasets, compare prompt variants, and prepare future fine-tunes.",
                responsibilities=["dataset curation", "eval", "fine-tune preparation"],
                preferred_backends=["local-pipeline", "qwen"],
                verifier_required=True,
            ),
        }

    def get_status(self) -> dict:
        return {
            "role_count": len(self.roles),
            "role_names": list(self.roles.keys()),
            "local_first": True,
            "remote_fallback": True,
        }

    def format_summary(self) -> str:
        return ", ".join(self.roles.keys())
