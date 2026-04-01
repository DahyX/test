# -*- coding: utf-8 -*-
"""
ecc_bridge.py
Integrates the Claude Code ecosystem (Everything Claude Code) into Jarvis natively.
Dynamically parses agents and commands from the everything-claude-code-main directory
and exposes them as Jarvis actions with full access to the local Ollama backend.
"""

import os
import re
import ollama

ECC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "everything-claude-code-main")
AGENTS_DIR = os.path.join(ECC_DIR, "agents")
COMMANDS_DIR = os.path.join(ECC_DIR, "commands")

PLUGIN_NAME = "ecc_bridge"
PLUGIN_DESCRIPTION = "Bridge to Everything Claude Code ecosystem agents and commands"
PLUGIN_ACTIONS = []

_components = {}

def parse_frontmatter(content):
    match = re.search(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not match: 
        return {}, content
    yaml_text = match.group(1)
    body = match.group(2)
    meta = {}
    for line in yaml_text.split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip().strip('"\'')
    return meta, body

# Dynamically populate actions at module load
if os.path.exists(AGENTS_DIR):
    for f in os.listdir(AGENTS_DIR):
        if f.endswith(".md"):
            try:
                with open(os.path.join(AGENTS_DIR, f), "r", encoding="utf-8") as file:
                    content = file.read()
                    meta, body = parse_frontmatter(content)
                    action_name = f"ecc_agent_{f[:-3].replace('-', '_')}"
                    PLUGIN_ACTIONS.append(action_name)
                    _components[action_name] = {
                        "type": "agent",
                        "name": meta.get("name", f[:-3]),
                        "desc": meta.get("description", f"ECC Agent: {f[:-3]}"),
                        "prompt": content
                    }
            except Exception as e:
                print(f"[ECC Bridge] Error loading agent {f}: {e}")

if os.path.exists(COMMANDS_DIR):
    for f in os.listdir(COMMANDS_DIR):
        if f.endswith(".md"):
            try:
                with open(os.path.join(COMMANDS_DIR, f), "r", encoding="utf-8") as file:
                    content = file.read()
                    meta, body = parse_frontmatter(content)
                    action_name = f"ecc_cmd_{f[:-3].replace('-', '_')}"
                    PLUGIN_ACTIONS.append(action_name)
                    _components[action_name] = {
                        "type": "command",
                        "name": f[:-3],
                        "desc": meta.get("description", f"ECC Command: {f[:-3]}"),
                        "prompt": body
                    }
            except Exception as e:
                print(f"[ECC Bridge] Error loading command {f}: {e}")

def handle(action, params, jarvis):
    if action not in _components:
        return f"Error: Unknown ECC action {action}"
    
    comp = _components[action]
    query = params.get("query", "")
    context_data = params.get("context", "")
    
    prompt = comp["prompt"]
    if comp["type"] == "agent":
        prompt = f"You are an expert AI agent loaded from the Everything Claude Code ecosystem. Follow these instructions implicitly:\n\n{prompt}"
    else:
        prompt = f"You are tasked with executing the following Claude Code ecosystem command. Follow these instructions carefully:\n\n{prompt}"

    messages = [{"role": "system", "content": prompt}]
    
    user_content = ""
    if context_data:
        user_content += f"Additional Context provided:\n{context_data}\n\n"
    user_content += f"User Request: {query}" if query else "Execute your primary function."
    
    messages.append({"role": "user", "content": user_content})
        
    try:
        # We invoke ollama directly or via Jarvis's underlying context
        response = ollama.chat(model="llama3:8b", messages=messages)
        return response.get('message', {}).get('content', '').strip()
    except Exception as e:
        return f"ECC Bridge Error executing {action}: {e}"
