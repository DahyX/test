# -*- coding: utf-8 -*-
"""
deepseek_provider.py — Reasoning Client
Isolated wrapper for DeepSeek-R1 API generation.
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import time
from models.model_contracts import ModelRequest, ModelResponse, ProviderConfig
from providers.base_provider import BaseProvider

class DeepSeekProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.backend_name = "deepseek"
        self.model_name = "deepseek-reasoner"

    def execute(self, request: ModelRequest) -> ModelResponse:
        if not self.config.enabled or "missing" in self.config.api_key_env:
            return ModelResponse(
                success=False, backend_name=self.backend_name, model_name=self.model_name,
                content="", raw_response="", usage={}, latency_ms=0,
                error_message="DeepSeek API Key is missing or provider disabled."
            )

        start = time.time()
        url = f"{self.config.api_base}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": request.user_input}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }

        try:
            req = urllib.request.Request(url, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("Authorization", f"Bearer {self.config.api_key_env}")
            
            # Executable Placeholder for HTTP testing without burning credits
            if "mock" in self.config.api_key_env or "missing" in self.config.api_key_env:
                 return ModelResponse(
                    success=True, backend_name=self.backend_name, model_name=self.model_name,
                    content="[Mock DeepSeek Reasoning] This is a simulated high-depth analysis.",
                    raw_response="{}", usage={"total_tokens": 50},
                    latency_ms=int((time.time() - start) * 1000), error_message=""
                )
            
            data = json.dumps(payload).encode("utf-8")
            with urllib.request.urlopen(req, data=data, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode())
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return ModelResponse(
                    success=True, backend_name=self.backend_name, model_name=self.model_name,
                    content=content, raw_response=json.dumps(result),
                    usage=result.get("usage", {}),
                    latency_ms=int((time.time() - start) * 1000), error_message=""
                )
                
        except Exception as e:
            return ModelResponse(
                success=False, backend_name=self.backend_name, model_name=self.model_name,
                content="", raw_response="", usage={}, latency_ms=int((time.time() - start) * 1000),
                error_message=f"DeepSeek Network Error: {e}"
            )
