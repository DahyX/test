# -*- coding: utf-8 -*-
"""
benchmark_runner.py - Runs repeatable task validations against Jarvis.
"""


class BenchmarkRunner:
    def __init__(self):
        self.test_cases = [
            {
                "name": "help_routing",
                "query": "help",
                "must_include": "Supported commands:",
            },
            {
                "name": "claude_status",
                "query": "claude status",
                "must_include": "Claude inheritance is active in Jarvis.",
            },
            {
                "name": "local_status",
                "query": "status",
                "must_include": "Local Status:",
            },
            {
                "name": "greeting_response",
                "query": "hi",
                "must_not_include": "Safe local chat fallback achieved.",
            },
        ]

    def run_suite(self, loop_instance) -> dict:
        """
        Runs the standard suite against the provided AgentLoop instance.
        """
        results = []
        passed = 0
        total = len(self.test_cases)

        for case in self.test_cases:
            output = loop_instance.run_cycle(case["query"])
            must_include = case.get("must_include")
            must_not_include = case.get("must_not_include")

            passed_case = True
            if must_include and must_include not in output:
                passed_case = False
            if must_not_include and must_not_include in output:
                passed_case = False

            if passed_case:
                passed += 1

            results.append(
                {
                    "name": case["name"],
                    "query": case["query"],
                    "passed": passed_case,
                    "output_preview": output[:160],
                }
            )

        return {
            "success_rate": passed / total if total > 0 else 0.0,
            "passed": passed,
            "total": total,
            "cases": results,
        }
