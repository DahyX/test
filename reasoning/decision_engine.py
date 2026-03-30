# -*- coding: utf-8 -*-
"""
decision_engine.py — The core action selector.
Uses the parsed intent and context from RuntimeState to pick a single ActionCandidate or generate a plan.
"""

from core.runtime_state import RuntimeState, ActionCandidate
import ollama
import json
from typing import Optional

class DecisionEngine:
    def __init__(self, reasoning_model: str = "llama3:8b"):
        self.model = reasoning_model
        
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
            res = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={"temperature": 0.1, "num_predict": 150}
            )
            data = json.loads(res.message.content)
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
