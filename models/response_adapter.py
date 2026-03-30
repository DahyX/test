# -*- coding: utf-8 -*-
"""
response_adapter.py — JSON Normalizer
Currently vestigial, as BaseProvider interfaces require providers to return strict ModelResponse.
Can be expanded to parse custom DeepSeek reasoning tags (<think>) before returning to Jarvis.
"""

from models.model_contracts import ModelResponse
import re

class ResponseAdapter:
    def __init__(self):
        pass

    def normalize(self, response: ModelResponse) -> ModelResponse:
        """
        Strips wrapper tags (like DeepSeek's <think>) or cleans artifact markdown before memory insertion.
        """
        if not response.success:
            return response
            
        if response.backend_name == "deepseek":
            # Example: Strip extensive thinking artifacts if they confuse the parser
            clean_content = re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL)
            response.content = clean_content.strip()

        return response
