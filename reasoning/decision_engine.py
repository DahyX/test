# -*- coding: utf-8 -*-
"""
decision_engine.py — The core action selector.
Uses the parsed intent and context from RuntimeState to pick a single ActionCandidate or generate a plan.
"""

from core.runtime_state import RuntimeState, ActionCandidate
from models.model_router import ModelRouter
from models.model_contracts import ModelRequest, TaskType
import json
import re
from typing import Optional

class DecisionEngine:
    def __init__(self, reasoning_model: str = "llama3:8b"):
        self.router = ModelRouter()
        
    def decide(self, state: RuntimeState) -> Optional[ActionCandidate]:
        """
        Decides what to do next. If it's pure chat, returns an ActionCandidate for 'respond'.
        If it requires multi-step planning, returns an ActionCandidate for 'plan'.
        If it's a direct command, returns an ActionCandidate for the specific tool.
        """
        # 1. Very basic routing right now.
        if state.task_type == "chat":
            return ActionCandidate(
                tool_name="respond",
                params={"text": state.user_input},
                expected_result="User is answered naturally.",
                risk_level="low"
            )
            
        # 2. Heuristics for direct OS commands
        text = state.user_input.lower()
        if text.startswith("open "):
            return ActionCandidate(
                tool_name="desktop",
                params={"cmd": "open", "app": text.replace("open ", "").strip()},
                expected_result=f"Application opened",
                risk_level="medium"
            )
            
        # 3. LLM-based Tool router
        prompt = f"""
        Given the intent: "{state.parsed_intent}"
        And goal: "{state.goal}"
        Choose the best action. Return JSON:
        {{
            "tool_name": "desktop|web|memory|plan|respond",
            "params": {{"key": "value"}},
            "expected_result": "What should happen if successful?",
            "risk_level": "low|medium|high"
        }}
        """
        try:
            req = ModelRequest(user_input=prompt, task_type=TaskType.REASONING, temperature=0.1, max_tokens=200)
            res = self.router.route_request(req)
            
            if not res.success:
                raise Exception(res.error_message)

            content = res.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1]
                
            data = json.loads(content.strip())
            return ActionCandidate(
                tool_name=data.get("tool_name", "respond"),
                params=data.get("params", {}),
                expected_result=data.get("expected_result", "System processes input"),
                risk_level=data.get("risk_level", "low")
            )
        except Exception as e:
            print(f"[DecisionEngine] Error: {e}")
            return ActionCandidate(
                tool_name="respond",
                params={"text": state.user_input},
                expected_result="Safely fallback to answering",
                risk_level="low"
            )
