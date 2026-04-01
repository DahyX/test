# -*- coding: utf-8 -*-
"""
claude_inheritance.py - Runtime bridge for the bundled Claude codebases.

Jarvis ships with two Claude-oriented source trees:
1. everything-claude-code-main
2. Claude-Code-Extended-Source-main

This module makes that inheritance real inside the active Python runtime by:
- Loading ECC markdown commands and agents as executable prompt assets
- Cataloging Extended Source commands and bundled skills for visibility
- Mapping a few high-value Extended Source commands onto runnable ECC assets
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from models.model_contracts import ModelRequest, TaskType
from models.model_router import ModelRouter
from response_styler import ResponseStyler


@dataclass(frozen=True)
class ClaudeAsset:
    action: str
    name: str
    kind: str
    source_repo: str
    description: str
    prompt: str = ""
    path: str = ""
    runnable: bool = False
    target_action: str = ""


@dataclass(frozen=True)
class ClaudeRuntimeSnapshot:
    ecc_command_count: int
    ecc_agent_count: int
    ecc_skill_count: int
    cce_command_count: int
    cce_skill_count: int
    alias_count: int
    runnable_action_count: int
    sample_commands: Tuple[str, ...]
    sample_agents: Tuple[str, ...]


class ClaudeInheritanceBridge:
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ECC_DIR = os.path.join(ROOT_DIR, "everything-claude-code-main")
    ECC_COMMANDS_DIR = os.path.join(ECC_DIR, "commands")
    ECC_AGENTS_DIR = os.path.join(ECC_DIR, "agents")
    ECC_SKILLS_DIR = os.path.join(ECC_DIR, "skills")

    CCE_DIR = os.path.join(ROOT_DIR, "Claude-Code-Extended-Source-main")
    CCE_COMMANDS_DIR = os.path.join(CCE_DIR, "commands")
    CCE_BUNDLED_SKILLS_DIR = os.path.join(CCE_DIR, "skills", "bundled")

    CCE_COMMAND_ALIASES = {
        "review": "ecc_cmd_code_review",
        "security-review": "ecc_agent_security_reviewer",
        "ultraplan": "ecc_cmd_prp_plan",
        "advisor": "ecc_agent_architect",
    }

    def __init__(self) -> None:
        self.assets: Dict[str, ClaudeAsset] = {}
        self.ecc_command_names: List[str] = []
        self.ecc_agent_names: List[str] = []
        self.cce_command_names: List[str] = []
        self.cce_skill_names: List[str] = []
        self.ecc_skill_count = 0
        self._load_assets()
        self.snapshot = self._build_snapshot()

    def list_action_names(self) -> List[str]:
        return sorted(self.assets.keys())

    def resolve_slash_action(self, command_name: str) -> Optional[str]:
        normalized = command_name.strip().lower().replace("_", "-")
        cce_action = f"cce_cmd_{normalized.replace('-', '_')}"
        if cce_action in self.assets:
            return cce_action

        ecc_action = f"ecc_cmd_{normalized.replace('-', '_')}"
        if ecc_action in self.assets:
            return ecc_action

        return None

    def resolve_agent_action(self, agent_name: str) -> Optional[str]:
        normalized = agent_name.strip().lower().replace("_", "-")
        action = f"ecc_agent_{normalized.replace('-', '_')}"
        if action in self.assets:
            return action
        return None

    def execute_action(self, action: str, query: str = "", context: str = "", jarvis=None) -> str:
        asset = self.assets.get(action)
        if not asset:
            return f"Unknown inherited Claude action: {action}"

        if asset.kind == "status":
            section = query.strip().lower() if query else "summary"
            return self.format_status(section=section)

        if asset.kind == "alias":
            alias_context = f"Requested via inherited alias /{asset.name}"
            merged_context = alias_context if not context else f"{alias_context}\n{context}"
            return self.execute_action(
                asset.target_action,
                query=query,
                context=merged_context,
                jarvis=jarvis,
            )

        if not asset.runnable:
            return (
                f"Inherited Claude asset '{asset.name}' is cataloged from {asset.path}, "
                "but it is not executable from Jarvis's Python runtime yet."
            )

        router = getattr(jarvis, "model_router", None) or ModelRouter()
        styler = getattr(jarvis, "response_styler", None) or ResponseStyler()

        request = ModelRequest(
            user_input=self._compose_prompt(asset, query=query, context=context),
            task_type=self._select_task_type(asset),
        )
        response = router.route_request(request)

        if response.success and response.content.strip():
            return styler.style(response.content.strip(), mode=self._select_style_mode(asset))

        return (
            f"Jarvis resolved inherited Claude {asset.kind} '{asset.name}' from {asset.path}, "
            f"but model execution failed: {response.error_message or 'unknown error'}"
        )

    def get_runtime_status(self) -> Dict[str, object]:
        return {
            "model_label": "Jarvis V6 + Claude Inheritance",
            "ecc_command_count": self.snapshot.ecc_command_count,
            "ecc_agent_count": self.snapshot.ecc_agent_count,
            "ecc_skill_count": self.snapshot.ecc_skill_count,
            "cce_command_count": self.snapshot.cce_command_count,
            "cce_skill_count": self.snapshot.cce_skill_count,
            "alias_count": self.snapshot.alias_count,
            "sample_commands": list(self.snapshot.sample_commands),
            "sample_agents": list(self.snapshot.sample_agents),
        }

    def format_status(self, section: str = "summary") -> str:
        section = (section or "summary").lower()

        if section == "commands":
            runnable = ", ".join(f"/{name}" for name in self.ecc_command_names[:18]) or "None"
            catalog = ", ".join(self.cce_command_names[:12]) or "None"
            return (
                "Inherited Claude commands loaded into Jarvis:\n"
                f"- Runnable ECC slash commands: {runnable}\n"
                f"- Cataloged Extended Source commands: {catalog}\n"
                "- High-value aliases wired in: /review, /security-review, /ultraplan, /advisor"
            )

        if section == "agents":
            agents = ", ".join(f"@{name}" for name in self.ecc_agent_names[:18]) or "None"
            return (
                "Inherited Claude agents loaded into Jarvis:\n"
                f"- Runnable ECC agents: {agents}\n"
                "- Example usage: @architect redesign the runtime bridge"
            )

        if section == "skills":
            skills = ", ".join(self.cce_skill_names[:12]) or "None"
            return (
                "Inherited Claude skill catalog:\n"
                f"- ECC skills discovered: {self.snapshot.ecc_skill_count}\n"
                f"- Extended Source bundled skills discovered: {self.snapshot.cce_skill_count}\n"
                f"- Sample Extended Source skills: {skills}"
            )

        return (
            "Claude inheritance is active in Jarvis.\n"
            f"- everything-claude-code-main contributes {self.snapshot.ecc_command_count} runnable commands and "
            f"{self.snapshot.ecc_agent_count} runnable agents.\n"
            f"- Runnable ECC assets total: {self.snapshot.ecc_command_count} commands, "
            f"{self.snapshot.ecc_agent_count} agents.\n"
            f"- Claude-Code-Extended-Source-main contributes a catalog of "
            f"{self.snapshot.cce_command_count} commands, {self.snapshot.cce_skill_count} bundled skills.\n"
            f"- ECC skills discovered for future wiring: {self.snapshot.ecc_skill_count}.\n"
            "- Quick start: /plan <task>, /tdd <task>, /code-review <scope>, /verify <task>, "
            "@architect <task>, @security-reviewer <task>.\n"
            "- Extended Source aliases wired into Jarvis: /review -> /code-review, "
            "/security-review -> @security-reviewer, /ultraplan -> /prp-plan, /advisor -> @architect."
        )

    def _load_assets(self) -> None:
        self.assets["claude_catalog_status"] = ClaudeAsset(
            action="claude_catalog_status",
            name="claude-catalog-status",
            kind="status",
            source_repo="jarvis",
            description="Describe inherited Claude assets currently wired into Jarvis.",
        )

        self._load_ecc_markdown_assets(
            base_dir=self.ECC_COMMANDS_DIR,
            prefix="ecc_cmd",
            kind="command",
            target_names=self.ecc_command_names,
        )
        self._load_ecc_markdown_assets(
            base_dir=self.ECC_AGENTS_DIR,
            prefix="ecc_agent",
            kind="agent",
            target_names=self.ecc_agent_names,
        )

        self.ecc_skill_count = self._count_skill_directories(self.ECC_SKILLS_DIR)
        self.cce_command_names = self._list_cce_commands()
        self.cce_skill_names = self._list_cce_skills()
        self._register_cce_aliases()

    def _build_snapshot(self) -> ClaudeRuntimeSnapshot:
        alias_count = sum(1 for asset in self.assets.values() if asset.kind == "alias")
        runnable_actions = sum(1 for asset in self.assets.values() if asset.runnable)

        return ClaudeRuntimeSnapshot(
            ecc_command_count=len(self.ecc_command_names),
            ecc_agent_count=len(self.ecc_agent_names),
            ecc_skill_count=self.ecc_skill_count,
            cce_command_count=len(self.cce_command_names),
            cce_skill_count=len(self.cce_skill_names),
            alias_count=alias_count,
            runnable_action_count=runnable_actions,
            sample_commands=tuple(self.ecc_command_names[:6]),
            sample_agents=tuple(self.ecc_agent_names[:6]),
        )

    def _load_ecc_markdown_assets(
        self,
        base_dir: str,
        prefix: str,
        kind: str,
        target_names: List[str],
    ) -> None:
        if not os.path.isdir(base_dir):
            return

        for filename in sorted(os.listdir(base_dir)):
            if not filename.endswith(".md"):
                continue

            path = os.path.join(base_dir, filename)
            content = self._read_text(path)
            meta, body = self._parse_frontmatter(content)
            slug = filename[:-3]
            action = f"{prefix}_{slug.replace('-', '_')}"
            description = meta.get("description") or f"Inherited Claude {kind}: {slug}"

            self.assets[action] = ClaudeAsset(
                action=action,
                name=slug,
                kind=kind,
                source_repo="everything-claude-code-main",
                description=description,
                prompt=body.strip() or content.strip(),
                path=path,
                runnable=True,
            )
            target_names.append(slug)

    def _register_cce_aliases(self) -> None:
        for command_name, target_action in self.CCE_COMMAND_ALIASES.items():
            if target_action not in self.assets:
                continue

            source_path = self._find_cce_command_path(command_name)
            description = self._extract_ts_description(source_path) if source_path else ""
            if not description:
                description = f"Alias inherited from Claude-Code-Extended-Source-main/{command_name}"

            action = f"cce_cmd_{command_name.replace('-', '_')}"
            self.assets[action] = ClaudeAsset(
                action=action,
                name=command_name,
                kind="alias",
                source_repo="Claude-Code-Extended-Source-main",
                description=description,
                path=source_path or f"{self.CCE_COMMANDS_DIR}/{command_name}",
                target_action=target_action,
            )

    def _find_cce_command_path(self, command_name: str) -> Optional[str]:
        direct_candidates = [
            os.path.join(self.CCE_COMMANDS_DIR, f"{command_name}.ts"),
            os.path.join(self.CCE_COMMANDS_DIR, f"{command_name}.tsx"),
            os.path.join(self.CCE_COMMANDS_DIR, f"{command_name}.js"),
            os.path.join(self.CCE_COMMANDS_DIR, f"{command_name}.jsx"),
        ]
        for candidate in direct_candidates:
            if os.path.isfile(candidate):
                return candidate

        nested_dir = os.path.join(self.CCE_COMMANDS_DIR, command_name)
        if os.path.isdir(nested_dir):
            for entry in ("index.ts", "index.tsx", "index.js", "index.jsx"):
                candidate = os.path.join(nested_dir, entry)
                if os.path.isfile(candidate):
                    return candidate
        return None

    def _list_cce_commands(self) -> List[str]:
        if not os.path.isdir(self.CCE_COMMANDS_DIR):
            return []

        names = set()
        for entry in os.listdir(self.CCE_COMMANDS_DIR):
            full_path = os.path.join(self.CCE_COMMANDS_DIR, entry)
            if os.path.isdir(full_path):
                names.add(entry)
                continue

            stem, ext = os.path.splitext(entry)
            if ext.lower() in {".ts", ".tsx", ".js", ".jsx"} and stem not in {"createMovedToPluginCommand"}:
                names.add(stem)

        return sorted(names)

    def _list_cce_skills(self) -> List[str]:
        if not os.path.isdir(self.CCE_BUNDLED_SKILLS_DIR):
            return []

        names = []
        for entry in sorted(os.listdir(self.CCE_BUNDLED_SKILLS_DIR)):
            stem, ext = os.path.splitext(entry)
            if ext.lower() not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            if stem in {"index"} or stem.endswith("Content"):
                continue
            names.append(stem)
        return names

    def _count_skill_directories(self, base_dir: str) -> int:
        count = 0
        if not os.path.isdir(base_dir):
            return count

        for current_root, _, files in os.walk(base_dir):
            if "SKILL.md" in files:
                count += 1
        return count

    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, str], str]:
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", content, re.DOTALL)
        if not match:
            return {}, content

        frontmatter = match.group(1)
        body = match.group(2)
        meta: Dict[str, str] = {}

        for line in frontmatter.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip("\"'")

        return meta, body

    def _extract_ts_description(self, path: Optional[str]) -> str:
        if not path or not os.path.isfile(path):
            return ""

        content = self._read_text(path)
        patterns = [
            r"description:\s*`([^`]+)`",
            r"description:\s*\"([^\"]+)\"",
            r"description:\s*'([^']+)'",
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return " ".join(match.group(1).split())
        return ""

    def _compose_prompt(self, asset: ClaudeAsset, query: str, context: str) -> str:
        sections = [
            "Jarvis runtime note:",
            "You are executing an inherited Claude asset inside Jarvis's active Python runtime.",
            f"Source repo: {asset.source_repo}",
            f"Asset type: {asset.kind}",
            f"Asset name: {asset.name}",
        ]

        if asset.description:
            sections.append(f"Asset description: {asset.description}")

        sections.extend(
            [
                "Inherited instructions:",
                asset.prompt.strip(),
                "User request:",
                query.strip() or "Execute the asset's default workflow for Jarvis.",
            ]
        )

        if context.strip():
            sections.extend(["Jarvis context:", context.strip()])

        return "\n\n".join(sections)

    def _select_task_type(self, asset: ClaudeAsset) -> TaskType:
        name = asset.name.lower()
        coding_markers = (
            "review",
            "build",
            "fix",
            "refactor",
            "tdd",
            "verify",
            "docs",
            "python",
            "cpp",
            "rust",
            "go",
            "kotlin",
            "typescript",
            "java",
            "coverage",
            "skill",
            "implement",
        )
        reasoning_markers = ("plan", "architect", "planner", "advisor", "model-route")

        if any(marker in name for marker in coding_markers):
            return TaskType.CODING
        if any(marker in name for marker in reasoning_markers):
            return TaskType.REASONING
        return TaskType.CHAT

    def _select_style_mode(self, asset: ClaudeAsset) -> str:
        if "review" in asset.name or "security" in asset.name:
            return "research"
        return "chat"

    def _read_text(self, path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            return file.read()


@lru_cache(maxsize=1)
def get_claude_inheritance_bridge() -> ClaudeInheritanceBridge:
    return ClaudeInheritanceBridge()
