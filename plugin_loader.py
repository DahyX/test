# -*- coding: utf-8 -*-
"""
plugin_loader.py — Jarvis Plugin System
Drops a .py file into the plugins/ folder → auto-discovered tool.

Plugin contract:
    Each plugin file must define:
    - PLUGIN_NAME: str
    - PLUGIN_DESCRIPTION: str
    - PLUGIN_ACTIONS: list[str]  — action names this plugin handles
    - def handle(action: str, params: dict, jarvis) -> str

Example plugin file: plugins/weather.py
    PLUGIN_NAME = "weather"
    PLUGIN_DESCRIPTION = "Get current weather for a city"
    PLUGIN_ACTIONS = ["get_weather"]

    def handle(action, params, jarvis):
        city = params.get("city", "Cairo")
        # ... fetch and return weather
        return f"Weather in {city}: ..."
"""

import os
import importlib.util
from typing import Optional


PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")


class PluginLoader:
    """Discovers and manages Jarvis plugins."""

    def __init__(self):
        self._plugins = {}  # action → (module, metadata)
        os.makedirs(PLUGINS_DIR, exist_ok=True)
        self._discover()

    def _discover(self):
        """Scan plugins/ directory and load all valid plugins."""
        for fname in os.listdir(PLUGINS_DIR):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            path = os.path.join(PLUGINS_DIR, fname)
            try:
                spec = importlib.util.spec_from_file_location(fname[:-3], path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                # Validate contract
                required = ["PLUGIN_NAME", "PLUGIN_DESCRIPTION", "PLUGIN_ACTIONS", "handle"]
                if not all(hasattr(mod, a) for a in required):
                    print(f"[Plugins] Skipped {fname}: missing required attributes")
                    continue

                for action in mod.PLUGIN_ACTIONS:
                    self._plugins[action] = (mod, {
                        "name": mod.PLUGIN_NAME,
                        "description": mod.PLUGIN_DESCRIPTION,
                        "file": fname,
                    })
                    print(f"[Plugins] Loaded '{mod.PLUGIN_NAME}' → action '{action}'")

            except Exception as e:
                print(f"[Plugins] Failed to load {fname}: {e}")

    def can_handle(self, action: str) -> bool:
        return action in self._plugins

    def handle(self, action: str, params: dict, jarvis) -> Optional[str]:
        """Dispatch an action to the appropriate plugin."""
        if action not in self._plugins:
            return None
        mod, meta = self._plugins[action]
        try:
            return mod.handle(action, params, jarvis)
        except Exception as e:
            return f"[Plugin '{meta['name']}' error]: {e}"

    def list_plugins(self) -> str:
        """Return a formatted list of loaded plugins."""
        if not self._plugins:
            return "No plugins loaded. Drop .py files into the plugins/ folder."
        seen = {}
        for action, (mod, meta) in self._plugins.items():
            name = meta["name"]
            if name not in seen:
                seen[name] = {"description": meta["description"], "actions": []}
            seen[name]["actions"].append(action)

        lines = ["Loaded plugins:"]
        for name, info in seen.items():
            lines.append(f"  {name}: {info['description']}")
            lines.append(f"    Actions: {', '.join(info['actions'])}")
        return "\n".join(lines)

    def get_action_descriptions(self) -> list:
        """Return plugin actions in a format suitable for the LLM tool schema."""
        results = []
        for action, (_, meta) in sorted(self._plugins.items()):
            results.append({
                "action": action,
                "description": meta["description"],
            })
        return results
