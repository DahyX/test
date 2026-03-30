# -*- coding: utf-8 -*-
"""
runtime_state.py — The singular object passed through the V6 Agent Loop.
Defines strict data contracts for every layer.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

class MemoryContext:
    def __init__(self):
        self.semantic: str = ""
        self.episodic: str = ""
        self.procedural: str = ""
        self.working: str = ""
        
    def to_combined_string(self) -> str:
        parts = []
        if self.working: parts.append(f"[Working Memory]\n{self.working}")
        if self.semantic: parts.append(f"[Semantic Facts]\n{self.semantic}")
        if self.episodic: parts.append(f"[Recent Episodes]\n{self.episodic}")
        if self.procedural: parts.append(f"[Procedures]\n{self.procedural}")
        return "\n\n".join(parts)

class MemoryItem:
    def __init__(self, item_type: str, content: str, topic: str = "", metadata: Optional[Dict] = None):
        self.item_type = item_type  # "semantic", "episodic", "procedural"
        self.content = content
        self.topic = topic
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class ActionCandidate:
    def __init__(self, tool_name: str, params: dict, expected_result: str = "", risk_level: str = "low"):
        self.tool_name = tool_name
        self.params = params
        self.expected_result = expected_result
        self.risk_level = risk_level  # "low", "medium", "high"
        
class ReflectionResult:
    def __init__(self, success: bool, confidence: float, observed_result: str, needs_recovery: bool = False, recovery_action: Optional[str] = None):
        self.success = success
        self.confidence = confidence
        self.observed_result = observed_result
        self.needs_recovery = needs_recovery
        self.recovery_action = recovery_action

class RuntimeState:
    """
    The central intelligence packet that flows through the Jarvis V6 core loop.
    Modules MUST only read and edit this state object.
    """
    def __init__(self, user_input: str):
        # 1. Perception
        self.user_input: str = user_input
        self.parsed_intent: str = ""
        self.task_type: str = "chat"  # chat, command, planning, debug
        
        # 2. Context
        self.memory_context: MemoryContext = MemoryContext()
        self.active_constraints: List[str] = []
        
        # 3. Reasoning
        self.current_goal: str = ""
        self.selected_action: Optional[ActionCandidate] = None
        self.response_style: str = "natural"
        
        # 4. Action
        self.action_result: str = ""
        self.action_success: bool = False
        
        # 5. Reflection
        self.reflection: Optional[ReflectionResult] = None
        self.pending_memory_writes: List[Dict[str, Any]] = []  # To be flushed by MemoryRouter
        self.plan_queue: List[ActionCandidate] = []
        
        
        # Diagnostics
        self.loop_started_at = datetime.now()
        self.risk_score: float = 0.0
