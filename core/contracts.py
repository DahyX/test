# -*- coding: utf-8 -*-
"""
contracts.py — Core Typed Contracts for V6 Phase 3
Defines the absolute truth data structures passed between macro-layers.
Using standard Python dataclasses for rigid typing without external dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

# ── Uncertainty & Policy ──────────────────────────────────────────────────────

@dataclass
class UncertaintyProfile:
    ambiguity_score: float = 0.0
    factual_confidence: float = 1.0
    memory_confidence: float = 1.0
    tool_confidence: float = 1.0
    plan_confidence: float = 1.0
    overall_confidence: float = 1.0
    assumptions: List[str] = field(default_factory=list)
    requires_verification: bool = False

@dataclass
class ReasoningPolicy:
    response_mode: str = "chat"
    reasoning_depth: str = "shallow"
    retrieve_memory: bool = False
    use_tools: bool = False
    answer_style: str = "concise"
    verbosity: int = 1
    verification_required: bool = False
    caution_level: str = "low"

# ── Memory & Conversation ─────────────────────────────────────────────────────

@dataclass
class DialogueState:
    primary_goal: str = ""
    secondary_goals: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    current_stage: str = "early"
    preference_hints: List[str] = field(default_factory=list)
    emotional_tone_hint: str = "neutral"
    detail_preference: str = "normal"
    last_commitments: List[str] = field(default_factory=list)

@dataclass
class MemoryContextBundle:
    semantic_hits: List[str] = field(default_factory=list)
    episodic_hits: List[str] = field(default_factory=list)
    procedural_hits: List[str] = field(default_factory=list)
    synthesis: str = ""
    freshness_score: float = 1.0
    trust_score: float = 1.0
    contradiction_flags: List[str] = field(default_factory=list)

# ── Planning & Execution ──────────────────────────────────────────────────────

@dataclass
class ToolDecision:
    should_use_tools: bool = False
    selected_tools: List[str] = field(default_factory=list)
    rationale: str = ""
    confidence: float = 1.0
    fallback_strategy: str = ""

@dataclass
class ResponsePlan:
    target_structure: str = ""
    opening_strategy: str = ""
    sections: List[str] = field(default_factory=list)
    style_notes: str = ""
    verbosity: int = 1
    should_include_caveats: bool = False
    should_include_next_step: bool = False

# ── Subconscious & Evolution ──────────────────────────────────────────────────

@dataclass
class Lesson:
    lesson_type: str = "behavioral"
    trigger: str = ""
    recommendation: str = ""
    confidence: float = 1.0
    promote_to_procedural: bool = False

@dataclass
class ImprovementCandidate:
    target_scope: str = ""
    candidate_type: str = "heuristic"
    description: str = ""
    patch_hint: str = ""
    benchmark_required: bool = True
    approval_required: bool = True
    risk_level: str = "low"

@dataclass
class BehaviorBenchmarkResult:
    benchmark_name: str = ""
    passed: bool = False
    score: float = 0.0
    notes: str = ""
    regressions: List[str] = field(default_factory=list)
    suggested_followups: List[str] = field(default_factory=list)
