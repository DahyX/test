# -*- coding: utf-8 -*-
"""
backend_registry.py — Provider Dependency Injection
Holds the instantiated provider objects for lookup during routing execution.
"""

from typing import Dict, Optional
from config.model_config import load_model_config
from providers.base_provider import BaseProvider
from providers.deepseek_provider import DeepSeekProvider
from providers.llama_provider import LlamaProvider
from providers.qwen_coder_provider import QwenCoderProvider
from providers.ollama_provider import OllamaProvider

class BackendRegistry:
    def __init__(self):
        self._config = load_model_config()
        self._providers: Dict[str, BaseProvider] = {
            "deepseek": DeepSeekProvider(self._config.deepseek),
            "llama": LlamaProvider(self._config.llama),
            "qwen": QwenCoderProvider(self._config.qwen),
            "ollama": OllamaProvider(self._config.ollama),
        }

    def get_provider(self, backend_name: str) -> Optional[BaseProvider]:
        """Fetches the instancce of the requested backend execution adapter."""
        return self._providers.get(backend_name)

    def is_enabled(self, backend_name: str) -> bool:
        """Checks if the provider loaded an API key and is flagged as enabled."""
        p = self.get_provider(backend_name)
        return p is not None and p.config.enabled
