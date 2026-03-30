# -*- coding: utf-8 -*-
"""
desktop_actions.py — Wraps legacy V5 desktop orchestration into the V6 pipeline.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desktop import Desktop

class DesktopActions:
    def __init__(self):
        # We pass memory=None because V6 handles Action Logging structurally in the Reflection Engine
        self.engine = Desktop(memory=None)

    def execute(self, cmd: str, params: dict) -> str:
        """
        Translates V6 standard parameters to the legacy desktop controller.
        """
        try:
            if cmd == "open":
                app = params.get("app", "")
                self.engine.open_app(app)
                return f"[Desktop] Successfully opened {app}"
                
            elif cmd == "run":
                command = params.get("command", "")
                out = self.engine.run_command(command)
                return f"[Desktop] Command executed. Output:\n{out}"
                
            elif cmd == "type":
                text = params.get("text", "")
                self.engine.type(text)
                return f"[Desktop] Typed '{text}'"
                
            elif cmd == "hotkey":
                keys = params.get("keys", [])
                self.engine.hotkey(*keys)
                return f"[Desktop] Pressed hotkey {'+'.join(keys)}"
                
            elif cmd == "click":
                x = params.get("x")
                y = params.get("y")
                self.engine.click(x, y)
                return f"[Desktop] Clicked at {x}, {y}"
                
            return f"[Desktop] Invalid desktop command: {cmd}"
            
        except Exception as e:
            return f"[Desktop] Error executing {cmd}: {e}"
