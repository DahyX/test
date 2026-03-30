# -*- coding: utf-8 -*-
"""
tool_registry.py — Jarvis V5 Standardized Tool Ecosystem
Central hub for native tools and loaded plugins. Passes safe schemas to the Reasoner/Planner.
"""

class ToolRegistry:
    def __init__(self, plugin_loader=None):
        self.plugin_loader = plugin_loader
        self._native_tools = {
            "learn_topic": {"desc": "Learn a new topic from the web", "risk": "low", "confirm": False},
            "scrape": {"desc": "Scrape an exact URL", "risk": "low", "confirm": False},
            "browser": {"desc": "Open a URL in default browser", "risk": "low", "confirm": False},
            "desktop": {"desc": "Execute mouse/keyboard control", "risk": "high", "confirm": True},
            "read_code": {"desc": "Read local source code", "risk": "low", "confirm": False},
            "search_code": {"desc": "Search local project code", "risk": "low", "confirm": False},
            "self_improve": {"desc": "Generate and apply code patches", "risk": "high", "confirm": True},
            "rollback_patch": {"desc": "Revert the last code patch", "risk": "medium", "confirm": True},
            "run_tests": {"desc": "Run validation tests", "risk": "low", "confirm": False},
            "remind": {"desc": "Schedule a future reminder", "risk": "low", "confirm": False},
            "start_voice": {"desc": "Activate wake-word listening", "risk": "low", "confirm": False},
            "stop_voice": {"desc": "Deactivate voice loop", "risk": "low", "confirm": False}
        }

    def register_native(self, name: str, desc: str, risk: str = "low", confirm: bool = False):
        self._native_tools[name] = {"desc": desc, "risk": risk, "confirm": confirm}

    def get_all_tools(self) -> dict:
        """Merge native tools with dynamically loaded plugins."""
        tools = dict(self._native_tools)
        if self.plugin_loader:
            plugins = self.plugin_loader.get_action_descriptions()
            for p in plugins:
                tools[p["action"]] = {"desc": p["description"], "risk": "medium", "confirm": False}
        return tools

    def get_safe_tool_schema(self, autonomous_mode: bool = False) -> list:
        """
        Return tool schema (for Ollama `tools` argument).
        If autonomous_mode is True, filter out anything requiring confirmation.
        """
        tools = self.get_all_tools()
        safe_keys = []
        for name, meta in tools.items():
            if autonomous_mode and meta["confirm"]:
                continue
            safe_keys.append(name)

        return [{
            "type": "function",
            "function": {
                "name": "perform_action",
                "description": "Perform a Jarvis action (non-conversational tasks)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": safe_keys,
                            "description": "The action to execute"
                        },
                        "params": {
                            "type": "object",
                            "description": "Action parameters in JSON mapping"
                        },
                        "response": {
                            "type": "string",
                            "description": "What to say to the user about this action"
                        }
                    },
                    "required": ["action", "params", "response"]
                }
            }
        }]

    def requires_confirmation(self, action: str) -> bool:
        tools = self.get_all_tools()
        if action in tools:
            return tools[action]["confirm"]
        return False
