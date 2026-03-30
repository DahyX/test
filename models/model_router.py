# -*- coding: utf-8 -*-
"""
model_router.py — Master Abstraction Engine
Takes Jarvis' model requests, selects the backend rules, iterates over fallback queues gracefully, 
and returns the text output identically as if it had hit local Ollama.
"""

from models.model_contracts import ModelRequest, ModelResponse, ModelInvocationTrace
from models.backend_registry import BackendRegistry
from models.provider_health import ProviderHealthMonitor
from models.backend_selector import BackendSelector
from models.response_adapter import ResponseAdapter

class ModelRouter:
    def __init__(self):
        self.registry = BackendRegistry()
        self.health = ProviderHealthMonitor()
        self.selector = BackendSelector(self.registry, self.health)
        self.adapter = ResponseAdapter()

    def route_request(self, request: ModelRequest) -> ModelResponse:
        """
        The absolute gateway handling inference loops entirely independent of Jarvis' brain.
        Will iterate through fallback chains until a successful response (or exhaustion) occurs.
        """
        decision = self.selector.select_chain(request)
        attempted = []
        failure_reasons = []

        if decision.selected_backend == "none":
            return ModelResponse(
                success=False, backend_name="router_core", model_name="none",
                content="", raw_response="", usage={}, latency_ms=0,
                error_message="Hard failure: No healthy backends available in fallback chain."
            )

        # Loop through explicitly ordered priority fallbacks
        for backend_name in decision.fallback_chain:
            attempted.append(backend_name)
            provider = self.registry.get_provider(backend_name)
            
            if not provider:
                failure_reasons.append(f"Provider class {backend_name} not found in registry.")
                continue
                
            # Fire Request abstraction
            response = provider.execute(request)
            
            if response.success:
                self.health.record_success(backend_name)
                # Clean up <think> tags or artifacts before letting Jarvis parse the text
                return self.adapter.normalize(response)
            else:
                self.health.record_failure(backend_name, response.error_message)
                failure_reasons.append(f"{backend_name} execution failed: {response.error_message}")
                # Continue loop to next fallback array element

        # Complete Fallback Exhaustion
        trace = ModelInvocationTrace(
            request_id="route-" + request.task_type.value,
            task_type=request.task_type.value,
            selected_backend=decision.selected_backend,
            attempted_backends=attempted,
            success=False,
            failure_reasons=failure_reasons
        )
        
        return ModelResponse(
            success=False, backend_name="exhausted", model_name="exhausted",
            content="", raw_response="", usage={}, latency_ms=0,
            error_message=f"Model Router Exhausted all Fallbacks. Trace = {trace}"
        )
