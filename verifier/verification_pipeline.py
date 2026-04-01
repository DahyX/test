"""
verification_pipeline.py - Explicit verifier stages for Jarvis improvements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class VerificationStage:
    name: str
    objective: str
    required_artifacts: List[str]


@dataclass
class VerificationVerdict:
    approved: bool
    rollback_ready: bool
    reasons: List[str]


class VerificationPipeline:
    def __init__(self):
        self.stages = [
            VerificationStage("impact_analysis", "Confirm scope, risk, and success metric.", ["proposal", "target metric"]),
            VerificationStage("sandbox", "Test candidate change in isolation before adoption.", ["sandbox result"]),
            VerificationStage("tests", "Run relevant tests and compile checks.", ["test output"]),
            VerificationStage("benchmarks", "Compare baseline against candidate behavior.", ["benchmark comparison"]),
            VerificationStage("rollback_readiness", "Ensure backup or revert path exists.", ["rollback checkpoint"]),
            VerificationStage("post_change_review", "Summarize risks, findings, and lessons.", ["review note"]),
        ]

    def get_status(self) -> dict:
        return {
            "stage_count": len(self.stages),
            "stage_names": [stage.name for stage in self.stages],
        }

    def review_candidate(
        self,
        has_metric: bool,
        has_sandbox_result: bool,
        has_benchmark_result: bool,
        rollback_ready: bool,
    ) -> VerificationVerdict:
        reasons = []
        approved = True

        if not has_metric:
            approved = False
            reasons.append("Missing explicit target metric.")
        if not has_sandbox_result:
            approved = False
            reasons.append("Missing sandbox validation.")
        if not has_benchmark_result:
            approved = False
            reasons.append("Missing benchmark comparison.")
        if not rollback_ready:
            approved = False
            reasons.append("Missing rollback readiness.")

        if approved:
            reasons.append("Candidate satisfies the current verifier gate contract.")

        return VerificationVerdict(approved=approved, rollback_ready=rollback_ready, reasons=reasons)

    def format_summary(self) -> str:
        return ", ".join(stage.name for stage in self.stages)
