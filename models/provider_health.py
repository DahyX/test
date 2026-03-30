# -*- coding: utf-8 -*-
"""
provider_health.py — Resilience Tracker
Temporarily skips endpoints that are returning 500s or timeouts to speed up fallback loops.
"""

import time
from typing import Dict
from models.model_contracts import ProviderHealthStatus

class ProviderHealthMonitor:
    def __init__(self):
        self._health: Dict[str, ProviderHealthStatus] = {}
        self.lockout_duration_ms = 60000  # 1 minute backoff for dead APIs

    def _init_if_missing(self, backend: str):
        if backend not in self._health:
            self._health[backend] = ProviderHealthStatus(
                backend_name=backend,
                is_healthy=True,
                consecutive_failures=0,
                last_failure_reason="",
                last_check_ms=int(time.time() * 1000)
            )

    def is_healthy(self, backend: str) -> bool:
        """Evaluates if a backend should be skipped globally."""
        if backend == "ollama": return True # Local fallback never soft-locked
        
        self._init_if_missing(backend)
        status = self._health[backend]
        
        # If unhealthy, check if lockout expired to try again
        if not status.is_healthy:
            time_since_fail = int(time.time() * 1000) - status.last_check_ms
            if time_since_fail > self.lockout_duration_ms:
                # Tentatively allow passing
                return True 
            return False
            
        return True

    def record_success(self, backend: str):
        """Resets tracker to healthy."""
        self._init_if_missing(backend)
        self._health[backend].is_healthy = True
        self._health[backend].consecutive_failures = 0
        self._health[backend].last_check_ms = int(time.time() * 1000)

    def record_failure(self, backend: str, reason: str):
        """Hardens lockout counters."""
        self._init_if_missing(backend)
        state = self._health[backend]
        state.consecutive_failures += 1
        state.last_failure_reason = reason
        state.last_check_ms = int(time.time() * 1000)
        
        if state.consecutive_failures >= 2:
            state.is_healthy = False
