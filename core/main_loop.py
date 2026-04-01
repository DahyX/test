# -*- coding: utf-8 -*-
"""
main_loop.py - Jarvis control loop.

The live runtime wires inherited Claude assets into Jarvis and now includes
real handlers for benchmark, self-check, and conversational chat.
"""

import re
import time
import urllib.error
import urllib.request
from typing import Optional

from benchmarking.benchmark_runner import BenchmarkRunner
from core.change_history import ChangeHistoryStore
from core.claude_inheritance import get_claude_inheritance_bridge
from core.routing_models import RequestScope
from models.model_contracts import ModelRequest, TaskType
from models.model_router import ModelRouter
from plugin_loader import PluginLoader
from reasoning.intent_analyzer import IntentAnalyzer
from response_styler import ResponseStyler
from tool_registry import ToolRegistry


class AgentLoop:
    def __init__(self) -> None:
        self.analyzer = IntentAnalyzer()
        self.history_store = ChangeHistoryStore()
        self.model_router = ModelRouter()
        self.response_styler = ResponseStyler()
        self.plugin_loader = PluginLoader()
        self.tool_registry = ToolRegistry(plugin_loader=self.plugin_loader)
        self.claude_bridge = get_claude_inheritance_bridge()
        self.benchmark_runner = BenchmarkRunner()
        self.last_runtime_response = ""
        self._ollama_probe = {"checked_at": 0.0, "reachable": False}

    def get_runtime_status(self) -> dict:
        status = self.claude_bridge.get_runtime_status()
        status["tool_count"] = len(self.tool_registry.get_all_tools())
        status["chat_ready"] = self._has_any_model_backend()
        return status

    def _help_handler(self) -> str:
        runtime = self.get_runtime_status()
        chat_state = "ready" if runtime["chat_ready"] else "degraded"
        return (
            "Supported commands:\n"
            "- chat                    (general conversation)\n"
            "- patch history           (view local changes)\n"
            "- improvement history     (view self-improvement attempts)\n"
            "- benchmark               (run built-in regression checks)\n"
            "- help                    (this help)\n"
            "- self-check              (runtime diagnostics)\n"
            "- status                  (local status)\n\n"
            "Claude inheritance:\n"
            "- /plan <task>\n"
            "- /tdd <task>\n"
            "- /code-review <scope>\n"
            "- /verify <task>\n"
            "- @architect <task>\n"
            "- @planner <task>\n"
            "- claude status\n\n"
            f"Loaded inherited assets: {runtime['ecc_command_count']} ECC commands, "
            f"{runtime['ecc_agent_count']} ECC agents, {runtime['cce_command_count']} "
            f"Extended Source commands, {runtime['cce_skill_count']} Extended Source bundled skills.\n"
            f"Chat backend status: {chat_state}."
        )

    def run_benchmark(self) -> dict:
        return self.benchmark_runner.run_suite(self)

    def format_benchmark_report(self, results: dict) -> str:
        lines = [
            "Benchmark Results:",
            f"- Passed: {results.get('passed', 0)}/{results.get('total', 0)}",
            f"- Success rate: {results.get('success_rate', 0.0) * 100:.0f}%",
        ]

        for case in results.get("cases", []):
            status = "PASS" if case.get("passed") else "FAIL"
            lines.append(f"- {case.get('name')}: {status}")

        return "\n".join(lines)

    def _benchmark_handler(self) -> str:
        return self.format_benchmark_report(self.run_benchmark())

    def run_self_check(self) -> dict:
        runtime = self.get_runtime_status()
        chat_request = ModelRequest(user_input="hello", task_type=TaskType.CHAT, max_tokens=64)
        routing = self.model_router.selector.select_chain(chat_request)

        providers = {}
        for backend_name in ("deepseek", "llama", "qwen"):
            provider = self.model_router.registry.get_provider(backend_name)
            providers[backend_name] = {
                "enabled": provider.config.enabled if provider else False,
                "configured": self._has_real_api_key(backend_name),
                "healthy": self.model_router.health.is_healthy(backend_name) if provider else False,
            }

        providers["ollama"] = {
            "enabled": True,
            "configured": True,
            "healthy": True,
            "reachable": self._ollama_available(force_refresh=True),
        }

        return {
            "claude_assets_ok": runtime["ecc_command_count"] > 0 and runtime["ecc_agent_count"] > 0,
            "claude_commands": runtime["ecc_command_count"],
            "claude_agents": runtime["ecc_agent_count"],
            "claude_extended_commands": runtime["cce_command_count"],
            "claude_extended_skills": runtime["cce_skill_count"],
            "tool_count": runtime["tool_count"],
            "chat_ready": runtime["chat_ready"],
            "selected_backend": routing.selected_backend,
            "fallback_chain": routing.fallback_chain,
            "providers": providers,
        }

    def format_self_check(self, results: dict) -> str:
        provider_bits = []
        for backend_name, info in results.get("providers", {}).items():
            if backend_name == "ollama":
                provider_bits.append(
                    f"- {backend_name}: reachable={info.get('reachable')}, enabled={info.get('enabled')}"
                )
            else:
                provider_bits.append(
                    f"- {backend_name}: configured={info.get('configured')}, "
                    f"enabled={info.get('enabled')}, healthy={info.get('healthy')}"
                )

        readiness = "ready" if results.get("chat_ready") else "degraded"
        lines = [
            "Self-check summary:",
            f"- Claude inheritance: {'OK' if results.get('claude_assets_ok') else 'DEGRADED'} "
            f"({results.get('claude_commands')} commands, {results.get('claude_agents')} agents loaded)",
            f"- Extended Source catalog: {results.get('claude_extended_commands')} commands, "
            f"{results.get('claude_extended_skills')} skills discovered",
            f"- Tool registry: {results.get('tool_count')} actions visible",
            f"- Chat readiness: {readiness}",
            f"- Model routing preference: {results.get('selected_backend')} -> "
            f"{', '.join(results.get('fallback_chain', [])) or 'none'}",
        ]
        lines.extend(provider_bits)

        if not results.get("chat_ready"):
            lines.append(
                "- Why replies may feel weak: no reachable model backend was detected, so Jarvis falls back to local built-in responses."
            )

        return "\n".join(lines)

    def _self_check_handler(self) -> str:
        return self.format_self_check(self.run_self_check())

    def _dispatch_plugin_action(self, action: str, query: str = "", context: str = "") -> Optional[str]:
        if not self.plugin_loader.can_handle(action):
            return None
        return self.plugin_loader.handle(
            action,
            {"query": query, "context": context},
            self,
        )

    def _handle_slash_command(self, prompt: str) -> str:
        command_part = prompt[1:].strip()
        command_name, _, raw_args = command_part.partition(" ")
        args = raw_args.strip()

        action = self.claude_bridge.resolve_slash_action(command_name)
        if not action:
            samples = ", ".join(f"/{name}" for name in self.claude_bridge.snapshot.sample_commands)
            return f"Unknown Claude slash command '/{command_name}'. Try {samples}."

        response = self._dispatch_plugin_action(action, query=args, context=self.last_runtime_response)
        return response or f"Failed to execute inherited Claude command '/{command_name}'."

    def _handle_agent_invocation(self, prompt: str) -> str:
        agent_part = prompt[1:].strip()
        agent_name, _, raw_args = agent_part.partition(" ")
        args = raw_args.strip()

        action = self.claude_bridge.resolve_agent_action(agent_name)
        if not action:
            samples = ", ".join(f"@{name}" for name in self.claude_bridge.snapshot.sample_agents)
            return f"Unknown Claude agent '@{agent_name}'. Try {samples}."

        response = self._dispatch_plugin_action(action, query=args, context=self.last_runtime_response)
        return response or f"Failed to execute inherited Claude agent '@{agent_name}'."

    def _maybe_handle_claude_runtime(self, prompt: str) -> Optional[str]:
        stripped = prompt.strip()
        lowered = stripped.lower()

        if stripped.startswith("/"):
            return self._handle_slash_command(stripped)

        if stripped.startswith("@"):
            return self._handle_agent_invocation(stripped)

        use_agent_match = re.match(r"^use\s+([a-z0-9\-]+)\s+agent\b[: ]?(.*)$", stripped, re.IGNORECASE)
        if use_agent_match:
            agent_name = use_agent_match.group(1)
            args = use_agent_match.group(2).strip()
            return self._handle_agent_invocation(f"@{agent_name} {args}".strip())

        if re.search(r"\b(claude status|claude assets|what claude(?: code)? (?:was|is) inherited)\b", lowered):
            return self.claude_bridge.format_status("summary")

        if re.search(r"\b(list|show)\s+claude\s+commands\b", lowered):
            return self.claude_bridge.format_status("commands")

        if re.search(r"\b(list|show)\s+claude\s+agents\b", lowered):
            return self.claude_bridge.format_status("agents")

        if re.search(r"\b(list|show)\s+claude\s+skills\b", lowered):
            return self.claude_bridge.format_status("skills")

        return None

    def _has_real_api_key(self, backend_name: str) -> bool:
        provider = self.model_router.registry.get_provider(backend_name)
        if not provider:
            return False
        key = getattr(provider.config, "api_key_env", "")
        return provider.config.enabled and bool(key) and "missing" not in key

    def _ollama_available(self, force_refresh: bool = False) -> bool:
        now = time.time()
        if not force_refresh and now - self._ollama_probe["checked_at"] < 10:
            return self._ollama_probe["reachable"]

        provider = self.model_router.registry.get_provider("ollama")
        if not provider:
            self._ollama_probe = {"checked_at": now, "reachable": False}
            return False

        url = provider.config.api_base.rstrip("/") + "/api/tags"
        reachable = False
        try:
            with urllib.request.urlopen(url, timeout=1):
                reachable = True
        except (urllib.error.URLError, TimeoutError, ValueError):
            reachable = False
        except Exception:
            reachable = False

        self._ollama_probe = {"checked_at": now, "reachable": reachable}
        return reachable

    def _has_any_model_backend(self) -> bool:
        return any(self._has_real_api_key(name) for name in ("deepseek", "llama", "qwen")) or self._ollama_available()

    def _local_status_handler(self) -> str:
        summary = self.history_store.get_local_status_summary()
        runtime = self.get_runtime_status()
        recent_attempts = ", ".join(summary.recent_attempts[-3:]) if summary.recent_attempts else "None"
        return (
            "Local Status:\n"
            f"Modified files: {', '.join(summary.modified_files) if summary.modified_files else 'None'}\n"
            f"Successes: {summary.successful_changes}, Failures: {summary.failed_changes}\n"
            f"Claude commands loaded: {runtime['ecc_command_count']}\n"
            f"Claude agents loaded: {runtime['ecc_agent_count']}\n"
            f"Recent attempts: {recent_attempts}"
        )

    def _repo_code_handler(self) -> str:
        return (
            "Repository investigation detected. Ask for a specific file or use an inherited workflow like "
            "`/code-review core/main_loop.py` or `@architect redesign the runtime`."
        )

    def _select_chat_task_type(self, prompt: str) -> TaskType:
        lowered = prompt.lower()
        coding_markers = (
            "code",
            "bug",
            "fix",
            "refactor",
            "function",
            "class",
            "python",
            ".py",
            "review",
            "test",
        )
        reasoning_markers = ("why", "how", "plan", "design", "architecture", "should", "question")

        if any(marker in lowered for marker in coding_markers):
            return TaskType.CODING
        if any(marker in lowered for marker in reasoning_markers) or prompt.endswith("?"):
            return TaskType.REASONING
        return TaskType.CHAT

    def _compose_chat_prompt(self, prompt: str) -> str:
        if self.last_runtime_response:
            return (
                "You are Jarvis, a helpful coding assistant with inherited Claude workflows.\n\n"
                f"Previous Jarvis reply:\n{self.last_runtime_response}\n\n"
                f"User message:\n{prompt}\n\n"
                "Reply naturally and concretely."
            )
        return (
            "You are Jarvis, a helpful coding assistant with inherited Claude workflows.\n\n"
            f"User message:\n{prompt}\n\n"
            "Reply naturally and concretely."
        )

    def _chat_with_model(self, prompt: str) -> Optional[str]:
        if not self._has_any_model_backend():
            return None

        request = ModelRequest(
            user_input=self._compose_chat_prompt(prompt),
            task_type=self._select_chat_task_type(prompt),
            temperature=0.2,
            max_tokens=400,
        )
        response = self.model_router.route_request(request)

        if not response.success:
            return None

        text = (response.content or "").strip()
        if not text or "[Mock" in text:
            return None

        return self.response_styler.style(text, mode="chat")

    def _offline_chat_response(self, prompt: str) -> Optional[str]:
        lowered = prompt.lower().strip()

        if re.search(r"^(hi|hello|hey|hiya|yo|good morning|good evening)[!. ]*$", lowered):
            return (
                "Hi! I'm here. Ask me to inspect code, run `self-check`, show `claude status`, or use `/plan` to start a change."
            )

        if re.search(r"\b(thanks|thank you|thx)\b", lowered):
            return "You're welcome. I can review code, plan work, or diagnose the runtime next."

        if re.search(r"(who are you|what are you|your name)", lowered):
            runtime = self.get_runtime_status()
            return (
                "I'm Jarvis, your local coding assistant. Right now I'm running a Python control loop with "
                f"{runtime['ecc_command_count']} inherited Claude commands and {runtime['ecc_agent_count']} inherited Claude agents."
            )

        if re.search(r"^(bye|goodbye|see you|quit|exit)[!. ]*$", lowered):
            return "See you later."

        return None

    def _chat_handler(self, prompt: str) -> str:
        offline_response = self._offline_chat_response(prompt)
        if offline_response is not None:
            return offline_response

        model_response = self._chat_with_model(prompt)
        if model_response is not None:
            return model_response

        return (
            "I couldn't reach a conversational model backend just now, but Jarvis is still running. "
            "You can use built-in workflows like `claude status`, `self-check`, `/plan <task>`, "
            "`/tdd <task>`, or `/code-review <file>`."
        )

    def run_cycle(self, prompt: str) -> str:
        prompt = prompt.strip()
        if not prompt:
            return "Empty request."

        claude_response = self._maybe_handle_claude_runtime(prompt)
        if claude_response is not None:
            self.last_runtime_response = claude_response
            return claude_response

        decision = self.analyzer.analyze_intent(prompt)

        if "web_search" in decision.forbidden_sources:
            pass

        if decision.request_scope == RequestScope.HELP_REQUEST:
            self.last_runtime_response = self._help_handler()
            return self.last_runtime_response

        if decision.request_scope == RequestScope.BENCHMARK_REQUEST:
            self.last_runtime_response = self._benchmark_handler()
            return self.last_runtime_response

        if decision.request_scope == RequestScope.SELF_CHECK_REQUEST:
            self.last_runtime_response = self._self_check_handler()
            return self.last_runtime_response

        if decision.request_scope == RequestScope.LOCAL_STATUS:
            self.last_runtime_response = self._local_status_handler()
            return self.last_runtime_response

        if decision.request_scope == RequestScope.LOCAL_HISTORY:
            self.last_runtime_response = self.history_store.get_history_summary()
            return self.last_runtime_response

        if decision.request_scope == RequestScope.SELF_IMPROVEMENT_REQUEST:
            self.last_runtime_response = (
                "Self-improvement mode is gated for safety. Tell me the exact file and goal, or use `/plan` first so I can propose the change cleanly."
            )
            return self.last_runtime_response

        if decision.request_scope == RequestScope.REPO_CODE_QUESTION:
            self.last_runtime_response = self._repo_code_handler()
            return self.last_runtime_response

        if decision.request_scope == RequestScope.CHAT:
            self.last_runtime_response = self._chat_handler(prompt)
            return self.last_runtime_response

        self.last_runtime_response = "Unsupported request flow hit. Safely failing behavior execution."
        return self.last_runtime_response
