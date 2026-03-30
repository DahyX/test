# -*- coding: utf-8 -*-
"""
planner.py — Handles multi-step execution breakdown.
Instead of returning a single ActionCandidate, it returns a List of ActionCandidates.
"""

from core.runtime_state import RuntimeState, ActionCandidate
from models.model_router import ModelRouter
from models.model_contracts import ModelRequest, TaskType
import json
from typing import List

class Planner:
    def __init__(self, planning_model: str = "llama3:8b"):
        self.router = ModelRouter()

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
             req = ModelRequest(user_input=prompt, task_type=TaskType.REASONING, temperature=0.2, max_tokens=500)
             res = self.router.route_request(req)
             
             if not res.success:
                 raise Exception(res.error_message)
                 
             content = res.content
             if "```json" in content:
                 content = content.split("```json")[1].split("```")[0]
             elif "```" in content:
                 content = content.split("```")[1]
                 
             data = json.loads(content.strip())
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
