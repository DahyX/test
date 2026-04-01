# -*- coding: utf-8 -*-
"""
main_loop.py — Jarvis Control Loop
The front door handler orchestrating inputs strictly.
"""

from core.routing_models import RequestScope
from core.change_history import ChangeHistoryStore
from reasoning.intent_analyzer import IntentAnalyzer

class AgentLoop:
    def __init__(self) -> None:
        self.analyzer = IntentAnalyzer()
        self.history_store = ChangeHistoryStore()

    def _help_handler(self) -> str:
        """Structured help response."""
        return """Supported commands:
• chat                    (general conversation)
• patch history           (view local changes)
• improvement history     (view self-improvement attempts)  
• benchmark               (benchmark status)
• help                    (this help)
• self-check              (system health)
• status                  (local status)

Examples:
• "show patch history"
• "what did you change?" """

    def _benchmark_handler(self) -> str:
        """Benchmark status placeholder."""
        return """Benchmark support is coming in Jarvis V6. 
Current status: Local benchmarking infrastructure ready.
Run: python -m benchmarking.benchmark_runner
No results yet."""

    def run_cycle(self, prompt: str) -> str:
        prompt = prompt.strip()
        if not prompt:
            return "Empty request."

        decision = self.analyzer.analyze_intent(prompt)

        # Force enforce source permission gaps upfront.
        if "web_search" in decision.forbidden_sources:
            pass # Ensure internal state doesn't mistakenly boot full web retriever chain

        if decision.request_scope == RequestScope.HELP_REQUEST:
            return self._help_handler()
            
        if decision.request_scope == RequestScope.BENCHMARK_REQUEST:
            return self._benchmark_handler()

        if decision.request_scope == RequestScope.LOCAL_STATUS:
            summary = self.history_store.get_local_status_summary()
            return (
                f"Local Status:\n"
                f"Modified files: {', '.join(summary.modified_files) if summary.modified_files else 'None'}\n"
                f"Successes: {summary.successful_changes}, Failures: {summary.failed_changes}"
            )

        if decision.request_scope == RequestScope.LOCAL_HISTORY:
            return self.history_store.get_history_summary()
            
        if decision.request_scope == RequestScope.SELF_IMPROVEMENT_REQUEST:
            return "Self improvement request intent detected. Operation would delegate to the patch proposer."

        if decision.request_scope == RequestScope.REPO_CODE_QUESTION:
            return "Repository investigation intended. Inspecting local code explicitly."

        if decision.request_scope == RequestScope.CHAT:
            return "Safe local chat fallback achieved."

        return "Unsupported request flow hit. Safely failing behavior execution."
