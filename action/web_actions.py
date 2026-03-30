# -*- coding: utf-8 -*-
"""
web_actions.py — Wraps legacy V5 scraping logic into the V6 pipeline.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import Scraper

class WebActions:
    def __init__(self):
        self.engine = Scraper()

    def execute(self, cmd: str, params: dict) -> str:
        """
        Translates V6 parameters to legacy scaper methods.
        """
        try:
            url = params.get("url", "")
            
            if cmd == "search":
                query = params.get("query", "")
                results = self.engine.search_duckduckgo(query)
                return f"[Web] Search results for '{query}':\n{results}"
                
            elif cmd == "read":
                if not url: return "[Web] Error: 'url' parameter required for reading."
                text = self.engine.get_text(url)
                return f"[Web] Read {len(text)} chars from {url}\n{text[:2000]}"
                
            elif cmd == "links":
                filter_text = params.get("filter_text")
                links = self.engine.get_links(url, filter_text)
                return f"[Web] Links found on {url}:\n{links}"
                
            return f"[Web] Invalid web command: {cmd}"
            
        except Exception as e:
            return f"[Web] Error executing {cmd}: {e}"
