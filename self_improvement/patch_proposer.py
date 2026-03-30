# -*- coding: utf-8 -*-
"""
patch_proposer.py — Analyzes code weaknesses and generates constrained heuristic patches.
"""

import os
import json
import ollama

class PatchProposer:
    def __init__(self, model: str = "qwen2.5-coder:1.5b"):
        self.model = model

    def propose_patch(self, target_file: str, issue_description: str) -> dict:
        """
        Reads the target file and asks the LLM to generate a minimal patch.
        Returns a dict with 'target_snippet' and 'replacement'.
        """
        if not os.path.exists(target_file):
            return {"error": "Target file does not exist."}

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        prompt = f"""
        Analyze this Python module and suggest a minimal fix.
        ISSUE: {issue_description}
        FILE: {target_file}
        
        CURRENT CODE:
        ```python
        {content[:4000]}
        ```
        
        Respond with a JSON object:
        {{
            "target_snippet": "exact lines to replace (copy verbatim)",
            "replacement": "new code to replace the target snippet",
            "reason": "why this helps"
        }}
        """
        try:
             res = ollama.chat(
                 model=self.model,
                 messages=[{"role": "user", "content": prompt}],
                 format="json",
                 options={"temperature": 0.1, "num_predict": 500}
             )
             reply = res.message.content.strip()
             return json.loads(reply)
        except Exception as e:
             return {"error": str(e)}
