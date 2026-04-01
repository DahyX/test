"""
session_manager.py - Bounded autonomous work registry for Jarvis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AutonomousJobSpec:
    job_id: str
    objective: str
    cadence: str
    max_runtime_minutes: int
    requires_verifier: bool = True
    destructive_allowed: bool = False
    default_tools: List[str] = field(default_factory=list)


@dataclass
class AutonomousSessionRecord:
    timestamp: str
    trigger: str
    objective: str
    files_touched: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    tests_run: List[str] = field(default_factory=list)
    result_summary: str = ""
    accepted: bool = False
    rollback_status: str = "not_needed"


class AutonomousSessionManager:
    def __init__(self):
        self.jobs = [
            AutonomousJobSpec(
                job_id="review_recent_failures",
                objective="Summarize recent failed interactions and propose bounded fixes.",
                cadence="hourly",
                max_runtime_minutes=10,
                default_tools=["memory", "benchmarks", "repo_qa"],
            ),
            AutonomousJobSpec(
                job_id="consolidate_memory",
                objective="Prune duplicates, merge related lessons, and refresh working memory.",
                cadence="daily",
                max_runtime_minutes=15,
                default_tools=["memory"],
            ),
            AutonomousJobSpec(
                job_id="benchmark_model_routing",
                objective="Compare routing choices against benchmark expectations.",
                cadence="daily",
                max_runtime_minutes=20,
                default_tools=["model_router", "benchmarks", "verifier"],
            ),
            AutonomousJobSpec(
                job_id="curate_training_data",
                objective="Promote strong conversations and reject weak fallback traces.",
                cadence="daily",
                max_runtime_minutes=20,
                default_tools=["dataset_builder", "memory", "verifier"],
            ),
            AutonomousJobSpec(
                job_id="review_code_hotspots",
                objective="Inspect unstable files and propose refactors without auto-applying them.",
                cadence="weekly",
                max_runtime_minutes=30,
                default_tools=["repo_qa", "tests", "verifier"],
            ),
        ]
        self.rate_limits: Dict[str, int] = {
            "max_sessions_per_day": 24,
            "max_destructive_sessions_per_day": 0,
        }

    def get_status(self) -> dict:
        return {
            "job_count": len(self.jobs),
            "rate_limits": dict(self.rate_limits),
            "requires_verifier": sum(1 for job in self.jobs if job.requires_verifier),
        }

    def render_runbook(self) -> str:
        return ", ".join(job.job_id for job in self.jobs)
