# -*- coding: utf-8 -*-
"""
runtime_state.py — The Pipeline Vehicle
Defines the `RuntimeState` dataclass flowing through the 6-layer architecture.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.contracts import (
    UncertaintyProfile, ReasoningPolicy, DialogueState, MemoryContextBundle,
    ToolDecision, ResponsePlan, Lesson, ImprovementCandidate
)

@dataclass
class MemoryItem:
    item_type: str
    content: str
    topic: str = ""
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ActionCandidate:
    tool_name: str
    params: dict
    expected_result: str = ""
    risk_level: str = "low"

@dataclass
class ReflectionResult:
    success: bool
    evaluation: str = ""
    memory_updates: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class RuntimeState:
    # Phase 1 & 2 Core fields mapping
    raw_user_input: str
    normalized_input: str = ""
    parsed_intent: str = ""
    inferred_mode: str = "chat"
    current_goal: str = ""
    subgoal: str = ""

    # Sub-component tracking
    dialogue_state: DialogueState = field(default_factory=DialogueState)
    retrieved_memory: MemoryContextBundle = field(default_factory=MemoryContextBundle)
    memory_confidence: float = 1.0
    contradiction_flags: List[str] = field(default_factory=list)
    
    # Reasoning Models
    uncertainty_profile: UncertaintyProfile = field(default_factory=UncertaintyProfile)
    reasoning_policy: ReasoningPolicy = field(default_factory=ReasoningPolicy)
    tool_decision: ToolDecision = field(default_factory=ToolDecision)
    response_plan: ResponsePlan = field(default_factory=ResponsePlan)
    
    # Legacy Action execution bridging
    selected_action: Optional[ActionCandidate] = None
    action_result: str = ""
    reflection_result: Optional[ReflectionResult] = None
    plan_queue: List[ActionCandidate] = field(default_factory=list)
    
    # Reflections
    pending_lessons: List[Lesson] = field(default_factory=list)
    improvement_candidates: List[ImprovementCandidate] = field(default_factory=list)
    
    metadata: dict = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)

    def log(self, message: str):
        print(f"[RunState] {message}")
        self.logs.append(message)
