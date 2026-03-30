# -*- coding: utf-8 -*-
"""
base_provider.py — Abstract Interface
Enforces a standard execution pattern across all APIs.
"""

from abc import ABC, abstractmethod
from typing import Optional
from models.model_contracts import ModelRequest, ModelResponse, ProviderConfig

class BaseProvider(ABC):
    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def execute(self, request: ModelRequest) -> ModelResponse:
        """
        Takes a normalized Jarvis intent, formats it into provider-specific JSON,
        calls the network, and returns a universal ModelResponse.
        """
        pass
