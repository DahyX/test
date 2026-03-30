# -*- coding: utf-8 -*-
"""
model_contracts.py — Unifying Interfaces
Defines strict dataclasses used by the router to decouple Jarvis from specific LLM providers.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

class TaskType(Enum):
    REASONING = "reasoning"
    CHAT = "chat"
    CODING = "coding"
    UNKNOWN = "unknown"

class ReasoningDepth(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class BackendType(Enum):
    DEEPSEEK = "deepseek"
    LLAMA = "llama"
    QWEN = "qwen"
    OLLAMA = "ollama"

@dataclass
class ModelRequest:
    user_input: str
    task_type: TaskType
    normalized_input: str = ""
    reasoning_depth: ReasoningDepth = ReasoningDepth.NORMAL
    requires_code_model: bool = False
    requires_high_reasoning: bool = False
    manual_backend_override: str = ""
    temperature: float = 0.7
    max_tokens: int = 1500
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelResponse:
    success: bool
    backend_name: str
    model_name: str
    content: str
    raw_response: str
    usage: Dict[str, int]
    latency_ms: int
    error_message: str

@dataclass
class RoutingDecision:
    selected_backend: str
    selected_model: str
    reason: str
    fallback_chain: List[str]
    manual_override_used: bool

@dataclass
class BackendDescriptor:
    backend_name: str
    model_name: str
    provider_type: BackendType
    supported_task_types: List[TaskType]
    supports_streaming: bool
    priority: int

@dataclass
class ProviderConfig:
    api_base: str
    api_key_env: str
    timeout_seconds: int
    enabled: bool

@dataclass
class ProviderHealthStatus:
    backend_name: str
    is_healthy: bool
    consecutive_failures: int
    last_failure_reason: str
    last_check_ms: int

@dataclass
class FallbackPolicy:
    preferred_backend: str
    fallback_backends: List[str]
    retry_count: int = 3
    fail_open_to_local: bool = True

@dataclass
class ModelInvocationTrace:
    request_id: str
    task_type: str
    selected_backend: str
    attempted_backends: List[str]
    success: bool
    failure_reasons: List[str]
