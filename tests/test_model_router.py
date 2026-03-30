# -*- coding: utf-8 -*-
"""
test_model_router.py — Pytest suite verifying Open-Model execution rules.
"""

import pytest
from models.model_contracts import ModelRequest, TaskType
from models.model_router import ModelRouter
from models.provider_health import ProviderHealthMonitor
from models.backend_registry import BackendRegistry

def test_reasoning_task_routes_to_deepseek():
    router = ModelRouter()
    req = ModelRequest(user_input="Solve P=NP", task_type=TaskType.REASONING)
    decision = router.selector.select_chain(req)
    assert decision.selected_backend == "deepseek"
    assert "llama" in decision.fallback_chain

def test_chat_task_routes_to_llama():
    router = ModelRouter()
    req = ModelRequest(user_input="Hello?", task_type=TaskType.CHAT)
    decision = router.selector.select_chain(req)
    assert decision.selected_backend == "llama"

def test_coding_task_routes_to_qwen():
    router = ModelRouter()
    req = ModelRequest(user_input="def main():", task_type=TaskType.CODING)
    decision = router.selector.select_chain(req)
    assert decision.selected_backend == "qwen"
    assert "deepseek" in decision.fallback_chain

def test_unknown_task_falls_back_safely():
    router = ModelRouter()
    req = ModelRequest(user_input="???", task_type=TaskType.UNKNOWN)
    decision = router.selector.select_chain(req)
    assert decision.selected_backend == "llama"
    assert "ollama" in decision.fallback_chain

def test_manual_override_works():
    router = ModelRouter()
    req = ModelRequest(user_input="Code", task_type=TaskType.CODING, manual_backend_override="deepseek")
    decision = router.selector.select_chain(req)
    assert decision.selected_backend == "deepseek"
    assert decision.manual_override_used is True

def test_unhealthy_provider_is_skipped():
    router = ModelRouter()
    
    # Intentionally poison Llama
    router.health.record_failure("llama", "Timeout")
    router.health.record_failure("llama", "Timeout")
    assert router.health.is_healthy("llama") is False
    
    req = ModelRequest(user_input="Chat", task_type=TaskType.CHAT)
    decision = router.selector.select_chain(req)
    # Since Llama is dead, it should skip directly to Ollama
    assert decision.selected_backend == "ollama"

def test_model_router_execution_integration():
    router = ModelRouter()
    req = ModelRequest(user_input="Chat", task_type=TaskType.CHAT)
    res = router.route_request(req)
    
    # Since the default config has a missing Llama key, the intelligent router instantly falls back to Ollama.
    assert res.success is True
    assert res.backend_name == "ollama"
