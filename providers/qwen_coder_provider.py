# -*- coding: utf-8 -*-
"""
qwen_coder_provider.py — Codebase/Review Client
Isolated wrapper for Qwen2.5-Coder generation.
"""

import time
from models.model_contracts import ModelRequest, ModelResponse, ProviderConfig
from providers.base_provider import BaseProvider

class QwenCoderProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.backend_name = "qwen"
        self.model_name = "qwen2.5-coder-32b-instruct"

    def execute(self, request: ModelRequest) -> ModelResponse:
        start = time.time()
        
        if not self.config.enabled or "missing" in self.config.api_key_env:
            return ModelResponse(
                success=False, backend_name=self.backend_name, model_name=self.model_name,
                content="", raw_response="", usage={}, latency_ms=0,
                error_message="Qwen Coder API Key is missing or disabled."
            )

        return ModelResponse(
            success=True, backend_name=self.backend_name, model_name=self.model_name,
            content="```python\n# [Mock Qwen Coder] generated def main(): pass\n```",
            raw_response="{}", usage={"total_tokens": 20},
            latency_ms=int((time.time() - start) * 1000), error_message=""
        )
