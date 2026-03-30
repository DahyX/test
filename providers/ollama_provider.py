# -*- coding: utf-8 -*-
"""
ollama_provider.py — Local Offline Fallback Client
Provides absolute latency fallback using local compute.
"""

import time
import json
import urllib.request
from models.model_contracts import ModelRequest, ModelResponse, ProviderConfig
from providers.base_provider import BaseProvider

class OllamaProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.backend_name = "ollama"
        self.model_name = "qwen2.5-coder:1.5b" # Default fallback

    def execute(self, request: ModelRequest) -> ModelResponse:
        if not self.config.enabled:
            return ModelResponse(
                success=False, backend_name=self.backend_name, model_name=self.model_name,
                content="", raw_response="", usage={}, latency_ms=0,
                error_message="Ollama Local fallback disabled."
            )

        start = time.time()
        url = f"{self.config.api_base}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": request.user_input}],
            "stream": False
        }

        try:
            req = urllib.request.Request(url, method="POST")
            req.add_header("Content-Type", "application/json")
            data = json.dumps(payload).encode("utf-8")
            
            # Simple executable fallback logic. Uses standard lib to avoid missing dependencies.
            # If Ollama isn't actually bound to 11434, fallback will gracefully fail in error_msg.
            with urllib.request.urlopen(req, data=data, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode())
                content = result.get("message", {}).get("content", "")
                
                return ModelResponse(
                    success=True, backend_name=self.backend_name, model_name=self.model_name,
                    content=content, raw_response=json.dumps(result),
                    usage={}, latency_ms=int((time.time() - start) * 1000), error_message=""
                )
                
        except Exception as e:
            return ModelResponse(
                success=False, backend_name=self.backend_name, model_name=self.model_name,
                content="", raw_response="", usage={}, latency_ms=int((time.time() - start) * 1000),
                error_message=f"Local Ollama Fallback Failed: {e}"
            )
