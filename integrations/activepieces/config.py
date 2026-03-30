# -*- coding: utf-8 -*-
"""
config.py — Activepieces Environment Adapter
Loads integration tokens and URLs safely, defaulting to localhost for offline resilience.
"""

import os
from dataclasses import dataclass

@dataclass
class ActivepiecesConfig:
    api_url: str
    api_token: str
    default_timeout_ms: int
    auto_approve_safe_actions: bool
    max_retries: int

def load_config() -> ActivepiecesConfig:
    """Safely loads AP environment variables with strict fallback defaults."""
    return ActivepiecesConfig(
        api_url=os.environ.get("AP_API_URL", "http://localhost:3000/api/v1"),
        api_token=os.environ.get("AP_API_TOKEN", "mock-token-fallback"),
        default_timeout_ms=int(os.environ.get("AP_TIMEOUT_MS", "5000")),
        auto_approve_safe_actions=os.environ.get("AP_AUTO_APPROVE", "false").lower() == "true",
        max_retries=1
    )
