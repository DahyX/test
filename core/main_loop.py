# -*- coding: utf-8 -*-
"""
main_loop.py — The Jarvis V6 single continuous Runtime Loop.
"""

from core.runtime_state import RuntimeState
from reasoning.intent_analyzer import IntentAnalyzer
from reasoning.decision_engine import DecisionEngine
from reasoning.planner import Planner
from memory.memory_router import MemoryRouter
from perception.context_builder import ContextBuilder
from safety.safety_gate import SafetyGate
from action.action_router import ActionRouter
from reflection.reflection_engine import ReflectionEngine

class AgentLoop:
    def __init__(self):
        print("Initializing V6 Core Loop...")
        self.memory = MemoryRouter()
        
        # Will initialize other modules dynamically.
        model = "qwen2.5-coder:1.5b"
        self.intent = IntentAnalyzer(fast_model=model)
        self.reasoning = DecisionEngine(reasoning_model=model)
        self.planner = Planner(planning_model=model)
        self.context = ContextBuilder(self.memory)
        self.safety = SafetyGate()
        self.action = ActionRouter()
        self.reflection = ReflectionEngine()
        
    def step(self, user_input: str) -> str:
        """
        Executes one atomic trip through the 6-layer agent loop.
        """
        state = RuntimeState(user_input=user_input)
        
        # 1. Perceive (Parse intent)
        state = self.intent.analyze(state)
        
        # 2. Context (Gather specific memory)
        state = self.context.build(state)
        
        # 3. Reason (Decide next action OR process queue)
        if state.plan_queue:
            # If we are resuming a queue, check if previous step failed
            if state.reflection and not state.reflection.success:
                state.plan_queue.clear()
                state.selected_action = self.reasoning.decide(state)
            else:
                state.selected_action = state.plan_queue.pop(0)
        else:
            state.selected_action = self.reasoning.decide(state)
            
            # Intercept 'plan' decisions to populate the queue
            if state.selected_action and state.selected_action.tool_name == "plan":
                candidates = self.planner.create_plan(state)
                if candidates:
                    state.plan_queue.extend(candidates)
                    state.selected_action = state.plan_queue.pop(0)
            
        if not state.selected_action:
            return "No action candidate was generated."
            
        # 4. Safety Gate
        if not self.safety.is_safe(state.selected_action):
            state.plan_queue.clear()
            return "Action blocked by safety gate."
            
        # 5. Act
        state.action_result = self.action.execute(state.selected_action)
        
        # 6. Reflect
        state = self.reflection.evaluate(state)
        
        # 7. Write to Memory
        if state.reflection:
            self.memory.write_pending(state.pending_memory_writes)
        
        # Return what happened.
        result = f"[V6 Loop] Intent: {state.parsed_intent} | Tool assigned: {state.selected_action.tool_name}"
        return result

if __name__ == "__main__":
    loop = AgentLoop()
    print("V6 Pre-Alpha Loop Booted.")
    print(loop.step("What is the weather like today?"))
