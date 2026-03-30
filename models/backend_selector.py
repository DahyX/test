# -*- coding: utf-8 -*-
"""
backend_selector.py — Decision Algorithm
Resolves the ModelPolicies against ProviderHealth to generate the exact RoutingDecision.
"""

import logging
from models.model_contracts import ModelRequest, RoutingDecision, TaskType
from models.model_policies import ModelPolicies
from models.provider_health import ProviderHealthMonitor
from models.backend_registry import BackendRegistry

class BackendSelector:
    def __init__(self, registry: BackendRegistry, health_monitor: ProviderHealthMonitor):
        self.policies = ModelPolicies()
        self.registry = registry
        self.health = health_monitor

    def select_chain(self, request: ModelRequest) -> RoutingDecision:
        """Builds a verified fallback chain ensuring models are enabled and healthy."""
        
        # 1. Manual Override takes absolute priority
        if request.manual_backend_override:
            if self.registry.is_enabled(request.manual_backend_override):
                return RoutingDecision(
                    selected_backend=request.manual_backend_override,
                    selected_model="override-model",
                    reason="Manual Override Requested.",
                    fallback_chain=[request.manual_backend_override, "ollama"],
                    manual_override_used=True
                )
            # Default to tracking failed override and moving back to policy

        # 2. Extract Base Policy
        policy = self.policies.get_policy_for_task(request.task_type)
        
        # 3. Compile Healthy Chain
        potential_chain = [policy.preferred_backend] + policy.fallback_backends
        healthy_chain = []
        
        for backend in potential_chain:
            if self.registry.is_enabled(backend) and self.health.is_healthy(backend):
                healthy_chain.append(backend)
                
        # 4. Fallback to offline if API network totally blackouts
        if not healthy_chain and policy.fail_open_to_local:
            healthy_chain = ["ollama"]
            
        selected = healthy_chain[0] if healthy_chain else "none"

        return RoutingDecision(
            selected_backend=selected,
            selected_model="derived-from-registry",
            reason=f"Policy-derived chain for Enum={request.task_type.value}",
            fallback_chain=healthy_chain,
            manual_override_used=bool(request.manual_backend_override)
        )
