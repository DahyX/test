# -*- coding: utf-8 -*-
"""
planner.py — Handles multi-step execution breakdown.
Instead of returning a single ActionCandidate, it returns a List of ActionCandidates.
"""

from core.runtime_state import RuntimeState, ActionCandidate
import ollama
import json
from typing import List

class Planner:
    def __init__(self, planning_model: str = "llama3:8b"):
        self.model = planning_model

    def create_plan(self, state: RuntimeState) -> List[ActionCandidate]:
        """
        Creates a list of action steps based on the goal.
        """
        prompt = f"""
        Break down the following goal into steps.
        Goal: "{state.goal}"
        Context: "{state.memory_context.to_combined_string()[:2000]}"
        
        Return JSON format:
        {{
            "plan_id": "unique_string",
            "steps": [
                {{
                    "step_id": "step_1",
                    "tool": "desktop|web|memory|read_code|self_improve",
                    "params": {{"key": "value"}},
                    "expected_result": "Exact successful outcome",
                    "depends_on": [],
                    "sub_reflection_required": true/false,
                    "risk": "low|medium|high"
                }}
            ]
        }}
        """
        try:
             res = ollama.chat(
                 model=self.model,
                 messages=[{"role": "user", "content": prompt}],
                 format="json",
                 options={"temperature": 0.2, "num_predict": 300}
             )
             data = json.loads(res.message.content)
             steps = data.get("steps", [])
             
             candidates = []
             for step in steps:
                 # Injecting sub-reflection metadata into params
                 params = step.get("params", {})
                 params["_step_id"] = step.get("step_id", "unknown")
                 params["_depends_on"] = step.get("depends_on", [])
                 params["_sub_reflection"] = step.get("sub_reflection_required", False)
                 
                 candidates.append(ActionCandidate(
                     tool_name=step.get("tool", "respond"),
                     params=params,
                     expected_result=step.get("expected_result", ""),
                     risk_level=step.get("risk", "low")
                 ))
             return candidates
        except Exception as e:
             print(f"[Planner] Error: {e}")
             return [ActionCandidate("respond", {"text": "I failed to create a plan."})]
