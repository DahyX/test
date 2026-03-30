# -*- coding: utf-8 -*-
"""
main_loop.py — The Safe Jarvis V6 single continuous Runtime Loop.
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
from core.change_history import ChangeHistoryStore

class AgentLoop:
    def __init__(self):
        print("Initializing V6 Stabilized Core Loop...")
        self.memory = MemoryRouter()
        self.history = ChangeHistoryStore()
        
        # Will initialize other modules dynamically.
        model = "qwen2.5-coder:1.5b"
        self.intent = IntentAnalyzer()
        self.reasoning = DecisionEngine(reasoning_model=model)
        self.planner = Planner(planning_model=model)
        self.context = ContextBuilder(self.memory)
        self.safety = SafetyGate()
        self.action = ActionRouter()
        self.reflection = ReflectionEngine()
        
    def step(self, user_input: str) -> str:
        """
        Executes one atomic trip through the stabilized 6-layer agent loop.
        """
        user_input = user_input.strip()
        state = RuntimeState(user_input=user_input, raw_user_input=user_input)
        
        # 0. Route Request deterministically to prevent hallucinations
        decision = self.intent.evaluate(user_input)
        
        # 1. Hardware-level interception of local questions
        if decision.requires_local_state and decision.request_scope == "local_status":
            summary = self.history.generate_status_summary()
            if not summary.modified_files:
                return "No recorded file modifications."
            return f"I have successfully modified: {summary.modified_files}. Recent events: {summary.recent_attempts}"
            
        if decision.requires_local_state and decision.request_scope == "local_history":
            if not self.history.improvements:
                return "No autonomous improvements attempted in this session."
            return f"Improvement History: {self.history.improvements}"
        
        # 2. Context (Gather specific memory)
        state.metadata["forbidden_sources"] = decision.forbidden_sources
        state = self.context.build(state)
        
        # 3. Reason (Decide next action OR process queue)
        if state.plan_queue:
            if state.reflection_result and not state.reflection_result.success:
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
            
        # 4. Enforce Source Permission Blocks BEFORE tool execution
        tool_name = state.selected_action.tool_name
        if not decision.requires_tools and tool_name not in ["chat", "reply"]:
            state.plan_queue.clear()
            return f"Action blocked: Request scope '{decision.request_scope}' forbids tool execution."
            
        if tool_name == "web_search" and "web_search" in decision.forbidden_sources:
            state.plan_queue.clear()
            return f"Action blocked: Web search forbidden for '{decision.request_scope}' scope."
            
        # 5. Safety Gate
        if not self.safety.is_safe(state.selected_action):
            state.plan_queue.clear()
            return "Action blocked by critical safety gate."
            
        # 6. Act
        state.action_result = self.action.execute(state.selected_action)
        self.history.log_change(action_type=tool_name, target_file="system", status="success", reason="Tool executed")
        
        # 7. Reflect
        state = self.reflection.evaluate(state)
        
        # 8. Write to Memory
        if state.reflection_result:
            self.memory.write_pending(state.reflection_result.memory_updates)
        
        # Return what happened.
        result = f"Scope: {decision.request_scope} | Tool Executed: {state.selected_action.tool_name}"
        return result

if __name__ == "__main__":
    loop = AgentLoop()
    print("V6 Pre-Alpha Loop Booted.")
    print(loop.step("did you work on any files until now?"))
