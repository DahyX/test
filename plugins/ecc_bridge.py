# -*- coding: utf-8 -*-
"""
ecc_bridge.py

Thin plugin adapter that exposes the Claude inheritance bridge to Jarvis's
plugin system. This keeps the active runtime pointed at real inherited assets
instead of letting the bundled Claude repos sit unused on disk.
"""

from core.claude_inheritance import get_claude_inheritance_bridge


BRIDGE = get_claude_inheritance_bridge()

PLUGIN_NAME = "claude_inheritance"
PLUGIN_DESCRIPTION = "Runtime bridge to inherited Claude commands, agents, and aliases"
PLUGIN_ACTIONS = BRIDGE.list_action_names()


def handle(action, params, jarvis):
    params = params or {}
    query = params.get("query", "")
    context = params.get("context", "")
    return BRIDGE.execute_action(action, query=query, context=context, jarvis=jarvis)
