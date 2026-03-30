# -*- coding: utf-8 -*-
"""
code_actions.py — Wraps legacy V5 codebase management logic into the V6 pipeline.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codebase_manager import CodebaseManager

class CodeActions:
    def __init__(self):
        self.engine = CodebaseManager()

    def execute(self, cmd: str, params: dict) -> str:
        """
        Translates V6 parameters into legacy code inspection methods.
        """
        try:
            target = params.get("target", "")
            
            if cmd == "list_files":
                files = self.engine.list_project_files()
                # Just return summary to not blow up context
                return f"[Code] Found {len(files)} files. Top files:\n" + "\n".join([f['path'] for f in files[:20]])
                
            elif cmd == "read_file":
                if not target: return "[Code] Error: 'target' parameter required."
                content = self.engine.read_file(target)
                return f"[Code] Read {target} ({len(content)} chars):\n{content[:5000]}"
                
            elif cmd == "search":
                term = params.get("term", "")
                results = self.engine.search_code(term)
                return f"[Code] Search for '{term}':\n{results[:5]}"
                
            return f"[Code] Invalid code command: {cmd}"
            
        except Exception as e:
            return f"[Code] Error executing {cmd}: {e}"
