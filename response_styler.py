# -*- coding: utf-8 -*-
"""
response_styler.py — Jarvis V5 Stylistic Post-Processor
Enforces human-like tone and removes robotic retrieval language.
"""

import re

class ResponseStyler:
    def __init__(self):
        self.robotic_phrases = [
            r"based on the retrieved (knowledge|context|information|sources),?",
            r"according to the (information|sources|context) available,?",
            r"the provided context suggests,?",
            r"multiple sources indicate that",
            r"it appears that",
            r"from the semantic memory,?"
        ]
        
    def style(self, raw_text: str, mode: str = "chat") -> str:
        """Apply tone corrections to raw LLM output."""
        text = raw_text
        
        # Don't strip sourcing language if we are explicitly acting as a researcher
        if mode == "research":
            return text
            
        # Strip robotic preambles
        for pattern in self.robotic_phrases:
            # Case insensitive exact stripping
            text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
            
        # Capitalize the first letter if we mangled the start
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
            
        # Clean up stray punctuation left by regex
        if text.startswith(",") or text.startswith("."):
            text = text[1:].strip()
            if text and text[0].islower():
                text = text[0].upper() + text[1:]
                
        # Concise mode enforcement (brute force chop if generator failed)
        if mode == "concise":
            sentences = re.split(r'(?<=[.!?]) +', text)
            if len(sentences) > 2:
                text = " ".join(sentences[:2])

        return text.strip()
