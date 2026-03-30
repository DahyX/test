# -*- coding: utf-8 -*-
"""
intent_analyzer.py — Analyzes the raw input and populates the RuntimeState intent fields.
"""

from core.runtime_state import RuntimeState
import ollama
import json

class IntentAnalyzer:
    def __init__(self, fast_model: str = "llama3:8b"):
        self.fast_model = fast_model

    def analyze(self, state: RuntimeState) -> RuntimeState:
        """
        Populate intent, task_type, goal, and response_style on the state object.
        """
        # Fast regex overrides
        text = state.user_input.strip().lower()
        if text.startswith(("open", "run", "type", "press", "click", "search")):
            state.task_type = "command"
            state.goal = text
            state.parsed_intent = "User wants to execute a direct command."
            return state

        # LLM Intent Extraction
        prompt = f"""
        Analyze the text and return JSON:
        {{
            "intent": "Brief summary of what the user wants",
            "task_type": "chat|command|planning",
            "goal": "The ultimate objective",
            "response_style": "natural|concise|research"
        }}
        Text: '{state.user_input}'
        """
        try:
            res = ollama.chat(
                model=self.fast_model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={"temperature": 0.1, "num_predict": 100}
            )
            data = json.loads(res.message.content)
            state.parsed_intent = data.get("intent", "")
            state.task_type = data.get("task_type", "chat")
            state.goal = data.get("goal", state.user_input)
            state.response_style = data.get("response_style", "natural")
        except Exception as e:
            print(f"[IntentAnalyzer] Error: {e}")
            state.task_type = "chat"
            state.goal = state.user_input
        
        return state
