# -*- coding: utf-8 -*-
"""
model_config.py — Router Config Loader
Safely isolates all API keys and URLs.
"""

import os
from dataclasses import dataclass
from models.model_contracts import ProviderConfig

@dataclass
class SystemModelConfig:
    deepseek: ProviderConfig
    llama: ProviderConfig
    qwen: ProviderConfig
    ollama: ProviderConfig

def load_model_config() -> SystemModelConfig:
    """Provides safe defaults and maps environment API keys for the routing backends."""
    return SystemModelConfig(
        deepseek=ProviderConfig(
            api_base=os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
            api_key_env=os.environ.get("DEEPSEEK_API_KEY", "missing-deepseek-key"),
            timeout_seconds=30,
            enabled=os.environ.get("DEEPSEEK_ENABLED", "true").lower() == "true",
        ),
        llama=ProviderConfig(
             api_base=os.environ.get("LLAMA_API_BASE", "https://api.together.xyz/v1"), # Example generic host
             api_key_env=os.environ.get("LLAMA_API_KEY", "missing-llama-key"),
             timeout_seconds=15,
             enabled=os.environ.get("LLAMA_ENABLED", "true").lower() == "true",
        ),
        qwen=ProviderConfig(
             api_base=os.environ.get("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
             api_key_env=os.environ.get("QWEN_API_KEY", "missing-qwen-key"),
             timeout_seconds=20,
             enabled=os.environ.get("QWEN_ENABLED", "true").lower() == "true",
        ),
        ollama=ProviderConfig(
             api_base=os.environ.get("OLLAMA_API_BASE", "http://localhost:11434"),
             api_key_env="",
             timeout_seconds=60,
             enabled=True # Ollama fallback is always allowed by default
        )
    )
