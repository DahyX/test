# -*- coding: utf-8 -*-
"""
generator.py — Jarvis V5 Natural Generation Layer
Always sits between context retrieval and the final response.
Ensures Jarvis sounds like a natural, high-end AI assistant.
"""

import ollama
import json
from typing import Optional

SYSTEM_PROMPT = """You are Jarvis.

You are intelligent, natural, concise, and confident.
You speak like a real high-end AI assistant.
You do not sound academic unless explicitly asked.
You do not over-explain.
You avoid robotic phrases like "Based on the retrieved knowledge" or "It appears that".
You answer naturally, directly, and clearly.

Behavior rules:
- Prefer natural language over source-dump summaries.
- If context is available, use it silently to improve the answer.
- Only show citations when the user asks for sources, or when research mode is active.
- Be conversational by default.
- Be sharp, helpful, and slightly witty when appropriate.
"""

class Generator:
    def __init__(self, default_model: str = "llama3:8b"):
        self.default_model = default_model

    def generate(self, query: str, context: str = "", mode: str = "chat", options: dict = None, stream: bool = False):
        """
        Generate a natural response based on query, context, and mode.
        If stream=True, returns the ollama generator.
        """
        options = options or {"temperature": 0.7}
        
        # Adjust prompt based on mode
        prompt = SYSTEM_PROMPT
        if mode == "concise":
            prompt += "\nMODE: Be extremely brief. Answer in 1-2 sentences max."
        elif mode == "research":
            prompt += "\nMODE: Formal research mode. Be detailed, academic, and cite sources explicitly using [Number]."
        elif mode == "planner":
            prompt += "\nMODE: Analytical planning mode. Focus purely on steps and outcomes."
        elif mode == "action":
            prompt += "\nMODE: Execution mode. Briefly state the action being taken."
            
        messages = [{"role": "system", "content": prompt}]
        
        # Build the final prompt block
        user_msg = ""
        if context:
            user_msg += f"Available Context (use silently unless in research mode):\n{context}\n\n"
        user_msg += f"User: {query}"
        
        messages.append({"role": "user", "content": user_msg})

        try:
            response = ollama.chat(
                model=self.default_model,
                messages=messages,
                options=options,
                stream=stream
            )
            if stream: return response
            return response.message.content.strip()
        except Exception as e:
            print(f"[Generator] Error: {e}")
            return "I encountered a communication error while trying to process that."
