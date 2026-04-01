"""
plan_schema.py - Explicit plan objects for Jarvis cognitive work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ImprovementMetric:
    name: str
    baseline: str
    target: str
    evaluation_method: str
    pass_threshold: str


@dataclass
class VerificationGate:
    name: str
    pass_condition: str
    required: bool = True


@dataclass
class PlanStep:
    step_id: str
    description: str
    owner: str
    expected_artifacts: List[str] = field(default_factory=list)
    verification_gates: List[str] = field(default_factory=list)


@dataclass
class ExecutionBlueprint:
    objective: str
    steps: List[PlanStep] = field(default_factory=list)
    metrics: List[ImprovementMetric] = field(default_factory=list)
    rollback_strategy: str = ""
    bounded: bool = True

    def summary(self) -> str:
        step_names = ", ".join(step.step_id for step in self.steps)
        metric_names = ", ".join(metric.name for metric in self.metrics)
        return (
            f"Objective: {self.objective} | "
            f"Steps: {step_names or 'none'} | "
            f"Metrics: {metric_names or 'none'} | "
            f"Bounded: {self.bounded}"
        )
