# -*- coding: utf-8 -*-
"""
reflection_engine.py — Evaluates the action's success and generates Memory Writes.
"""

from core.runtime_state import RuntimeState, ReflectionResult
import ollama
import json

class ReflectionEngine:
    def __init__(self, model: str = "llama3:8b"):
        self.model = model
        
    def evaluate(self, state: RuntimeState) -> RuntimeState:
        """
        Analyzes the action result against the expected result.
        Produces a ReflectionResult and populates pending_memory_writes.
        """
        if not state.selected_action:
            return state
            
        action = state.selected_action
        
        prompt = f"""
        Action: {action.tool_name}
        Params: {json.dumps(action.params)}
        Expected Result: {action.expected_result}
        Actual Observed Result: {state.action_result}
        
        Evaluate the success of this action.
        Return JSON:
        {{
            "success": true/false,
            "confidence": 0.0 to 1.0,
            "reflection_notes": "Why it succeeded or failed",
            "needs_recovery": true/false,
            "suggested_memory_write": {{
                "type": "episodic|semantic|procedural",
                "content": "What to remember for next time"
            }},
            "should_store_memory": true/false
        }}
        """
        
        try:
             res = ollama.chat(
                 model=self.model,
                 messages=[{"role": "user", "content": prompt}],
                 format="json",
                 options={"temperature": 0.1, "num_predict": 200}
             )
             data = json.loads(res.message.content)
             
             state.reflection = ReflectionResult(
                 success=data.get("success", False),
                 confidence=data.get("confidence", 0.5),
                 observed_result=data.get("reflection_notes", ""),
                 needs_recovery=data.get("needs_recovery", False)
             )
             
             # Create pending memory writes
             if data.get("should_store_memory") and data.get("suggested_memory_write"):
                 mem = data["suggested_memory_write"]
                 state.pending_memory_writes.append({
                     "type": mem.get("type", "episodic"),
                     "data": {
                         "content": mem.get("content", ""),
                         "topic": state.goal,
                         "role": "system"
                     }
                 })
                 
             # Always log the action strictly
             state.pending_memory_writes.append({
                 "type": "action_log",
                 "data": {
                     "action_type": action.tool_name,
                     "params": json.dumps(action.params),
                     "result": state.action_result,
                     "success": state.reflection.success
                 }
             })

        except Exception as e:
             print(f"[Reflection] Error: {e}")
             state.reflection = ReflectionResult(
                 success=True, confidence=1.0, observed_result="Reflection failed."
             )
             
        return state
