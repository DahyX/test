"""
foundation.py - Live architectural foundation for next-generation Jarvis.

This module does not pretend Jarvis is already a full artificial mind. It
collects the concrete pieces that already exist, defines the next layers that
must be built, and exposes a runtime-readable status surface so progress stays
auditable.
"""

from __future__ import annotations

import os

from autonomy.session_manager import AutonomousSessionManager
from benchmarks.cognitive_regression import CognitiveRegressionSuite
from dataset_builder.jarvis_dataset_schema import JARVIS_DATASET_FILES
from model_stack.jarvis_model_stack import JarvisModelStack
from planning.plan_schema import ExecutionBlueprint, ImprovementMetric, PlanStep, VerificationGate
from rollback.rollback_controller import RollbackController
from training_pipeline.llm_course_pipeline import LLMCourseTrainingPipeline
from verifier.verification_pipeline import VerificationPipeline


class NextGenerationFoundation:
    def __init__(self, project_root: str, db_path: str = "jarvis_brain.db"):
        self.project_root = project_root
        self.model_stack = JarvisModelStack()
        self.verifier = VerificationPipeline()
        self.autonomy = AutonomousSessionManager()
        self.training = LLMCourseTrainingPipeline()
        self.rollback = RollbackController(db_path=db_path)
        self.regression = CognitiveRegressionSuite()
        self.blueprint = self._build_blueprint()

    def _build_blueprint(self) -> ExecutionBlueprint:
        metric = ImprovementMetric(
            name="benchmark_pass_rate",
            baseline="current focused suite baseline",
            target="improve pass rate or preserve it while raising capability",
            evaluation_method="run focused regression suite and compare benchmark traces",
            pass_threshold="candidate must not reduce benchmark pass rate",
        )
        gates = [
            VerificationGate("impact_analysis", "Scope and risks are explicit before edits"),
            VerificationGate("sandbox_validation", "Candidate change is tested in isolation"),
            VerificationGate("benchmark_check", "Target metrics are measured against baseline"),
            VerificationGate("rollback_ready", "Rollback artifact exists before merge"),
        ]
        steps = [
            PlanStep(
                step_id="observe",
                description="Collect failures, weak answers, and unstable routing behavior.",
                owner="reflection",
                expected_artifacts=["failure digest", "candidate list"],
                verification_gates=["impact_analysis"],
            ),
            PlanStep(
                step_id="propose",
                description="Create small, testable candidate improvements with explicit metrics.",
                owner="self_improvement",
                expected_artifacts=["change proposal", "benchmark plan"],
                verification_gates=["impact_analysis", "benchmark_check"],
            ),
            PlanStep(
                step_id="verify",
                description="Run verifier gates, regression checks, and rollback readiness checks.",
                owner="verifier",
                expected_artifacts=["verifier verdict", "rollback checkpoint"],
                verification_gates=["sandbox_validation", "rollback_ready"],
            ),
            PlanStep(
                step_id="adopt",
                description="Promote only improvements that measurably help Jarvis.",
                owner="executive",
                expected_artifacts=["accepted change log", "lessons learned"],
                verification_gates=["benchmark_check", "rollback_ready"],
            ),
        ]
        return ExecutionBlueprint(
            objective="Turn Jarvis into a persistent cognitive engineering system through measured iteration.",
            steps=steps,
            metrics=[metric],
            rollback_strategy="Reject or revert any change that fails benchmarks, verification, or safety review.",
            bounded=True,
        )

    def get_status(self) -> dict:
        data_dir = os.path.join(self.project_root, "data")
        present_dataset_files = [
            name for name in JARVIS_DATASET_FILES if os.path.exists(os.path.join(data_dir, name))
        ]
        return {
            "model_roles": len(self.model_stack.roles),
            "verifier_stages": len(self.verifier.stages),
            "autonomy_jobs": len(self.autonomy.jobs),
            "training_stages": len(self.training.stages),
            "benchmark_tracks": len(self.regression.definitions),
            "dataset_files_present": len(present_dataset_files),
            "dataset_files_expected": len(JARVIS_DATASET_FILES),
            "local_first": True,
            "real_now": [
                "offline memory",
                "repo-grounded QA",
                "Claude inheritance bridge",
                "LLM roadmap and dataset export",
                "web runtime status and streaming UI",
            ],
            "partial_now": [
                "model routing",
                "reflection engine",
                "scheduler",
                "rollback support",
                "self-improvement stubs",
            ],
            "aspirational": [
                "fully autonomous self-editing loops",
                "trained Jarvis-specific model family",
                "rich multi-pass internal reasoning pipeline",
                "continuous background evaluation and code improvement",
            ],
        }

    def format_status(self) -> str:
        status = self.get_status()
        return (
            "Jarvis cognitive foundation:\n"
            f"- Model roles defined: {status['model_roles']}\n"
            f"- Verifier stages defined: {status['verifier_stages']}\n"
            f"- Autonomy jobs defined: {status['autonomy_jobs']}\n"
            f"- Training stages defined: {status['training_stages']}\n"
            f"- Benchmark tracks defined: {status['benchmark_tracks']}\n"
            f"- Dataset files present: {status['dataset_files_present']}/{status['dataset_files_expected']}\n"
            f"- Local-first runtime: {status['local_first']}\n"
            f"- Model stack: {self.model_stack.format_summary()}\n"
            f"- Verifier: {self.verifier.format_summary()}\n"
            f"- Autonomy jobs: {self.autonomy.render_runbook()}\n"
            f"- Training pipeline: {self.training.format_summary()}\n"
            "Real now:\n"
            f"- {status['real_now'][0]}\n"
            f"- {status['real_now'][1]}\n"
            f"- {status['real_now'][2]}\n"
            f"- {status['real_now'][3]}\n"
            f"- {status['real_now'][4]}\n"
            "Partially real:\n"
            f"- {status['partial_now'][0]}\n"
            f"- {status['partial_now'][1]}\n"
            f"- {status['partial_now'][2]}\n"
            f"- {status['partial_now'][3]}\n"
            f"- {status['partial_now'][4]}\n"
            "Aspirational next:\n"
            f"- {status['aspirational'][0]}\n"
            f"- {status['aspirational'][1]}\n"
            f"- {status['aspirational'][2]}\n"
            f"- {status['aspirational'][3]}"
        )
