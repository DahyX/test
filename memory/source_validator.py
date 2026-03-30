# -*- coding: utf-8 -*-
"""
source_validator.py — External Tool Trust Scoring
Validates that web scrapes or retrieved local documents are trustworthy.
"""

from typing import Dict, Any

class SourceValidator:
    def __init__(self):
        self.blocklist = ["malware", "phishing", "unverified"]

    def validate(self, source_url: str, content: str) -> float:
        """
        Returns a trust score between 0.0 and 1.0 based on URL and content heuristics.
        """
        if any(bad in source_url.lower() for bad in self.blocklist):
            return 0.1
            
        if "error 404" in content.lower() or "captcha" in content.lower():
            return 0.3
            
        if source_url.startswith("file://") or source_url.startswith("localhost"):
            return 1.0 # High trust for local files
            
        # Default web trust
        return 0.8
