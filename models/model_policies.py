# -*- coding: utf-8 -*-
"""
model_policies.py — Static Routing Rulesets
Defines which task types execute on which models, making rules editable independently.
"""

from models.model_contracts import TaskType, FallbackPolicy

class ModelPolicies:
    def __init__(self):
        # Master mapping separating intent-type to fallback-chain rules.
        self.routing_table = {
            TaskType.REASONING: FallbackPolicy(
                preferred_backend="deepseek",
                fallback_backends=["llama", "ollama"]
            ),
            TaskType.CHAT: FallbackPolicy(
                preferred_backend="llama",
                fallback_backends=["ollama"]
            ),
            TaskType.CODING: FallbackPolicy(
                preferred_backend="qwen",
                fallback_backends=["deepseek", "ollama"]
            ),
            TaskType.UNKNOWN: FallbackPolicy(
                preferred_backend="llama",
                fallback_backends=["ollama"]
            )
        }

    def get_policy_for_task(self, task: TaskType) -> FallbackPolicy:
        """Looks up the strict fallback chain for a given Jarvis task requirement."""
        return self.routing_table.get(task, self.routing_table[TaskType.UNKNOWN])
