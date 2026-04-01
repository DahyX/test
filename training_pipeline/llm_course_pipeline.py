"""
llm_course_pipeline.py - Jarvis training pipeline grounded in mlabonne/llm-course.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class TrainingStage:
    name: str
    objective: str
    outputs: List[str]


class LLMCourseTrainingPipeline:
    SOURCE_URL = "https://github.com/mlabonne/llm-course"

    def __init__(self):
        self.stages = [
            TrainingStage("fundamentals", "Use the course material to ground implementation choices.", ["curriculum notes"]),
            TrainingStage("dataset_builder", "Create Jarvis-specific supervised datasets and eval sets.", ["jsonl datasets"]),
            TrainingStage("sft_qlora", "Run parameter-efficient supervised fine-tuning on a small open model.", ["adapter weights"]),
            TrainingStage("alignment", "Add ORPO or DPO style alignment after stable SFT.", ["preference checkpoints"]),
            TrainingStage("evaluation", "Score chat, coding, memory, verifier, and autonomy behavior.", ["evaluation reports"]),
            TrainingStage("quantization", "Export compact local builds for Jarvis deployment.", ["quantized artifacts"]),
            TrainingStage("deployment", "Route the best local/remote candidates into the Jarvis model stack.", ["deployment manifest"]),
        ]

    def get_status(self) -> dict:
        return {
            "source_url": self.SOURCE_URL,
            "stage_count": len(self.stages),
            "stage_names": [stage.name for stage in self.stages],
        }

    def format_summary(self) -> str:
        return ", ".join(stage.name for stage in self.stages)
