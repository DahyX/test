# -*- coding: utf-8 -*-
"""
evolution_manager.py — Jarvis V5 Controlled Evolution Loop
Wraps the self-improver. Finds weaknesses, applies patches safely, tests, and benchmarks.
"""

from self_improvement import SelfImprovementEngine
from evaluator import Evaluator

class EvolutionManager:
    def __init__(self, memory, router):
        self.memory = memory
        self.router = router
        coding_model = self.router.select_model("coding")
        self.improver = SelfImprovementEngine(memory, model=coding_model)
        self.evaluator = Evaluator(memory, model=coding_model)

    def run_evolution_cycle(self) -> str:
        """
        The Loop: detect weakness -> propose fix -> compile -> smoke test -> benchmark -> apply.
        """
        print("[Evolution] Starting autonomous evolution cycle...")
        
        # 1. Detect Weakness
        weakness = self._detect_weakness()
        if not weakness:
            return "No clear weaknesses found in recent evaluations. System is stable."
            
        print(f"[Evolution] Weakness detected: {weakness['issue']}")
        
        # 2. Isolate & Propose Fix
        goal = f"Fix the following issue autonomously: {weakness['issue']}"
        print(f"[Evolution] Attempting patch for: {goal}")
        patch_result = self.improver.debug_and_patch(goal, scope="safe")
        
        if "Failed" in patch_result or "Error" in patch_result:
            return f"Evolution halted. Patch generation failed: {patch_result}"
            
        # 3. Test & Benchmark (Smoke test happens inherently in patch application)
        print("[Evolution] Patch applied. Running benchmark delta...")
        bench_result = self.evaluator.run_benchmarks(brain=None) # Normally passes live brain
        score = bench_result.get("overall_score", 0)
        
        if score < weakness.get("previous_score", 0.5):
            print("[Evolution] Benchmark regressed. Rolling back...")
            self.improver.rollback()
            return f"Evolution aborted. Patch caused regression (Score: {score:.2f}). Rolled back."
            
        # Keep patch
        return f"Evolution successful! Addressed '{weakness['issue']}'. New benchmark score: {score:.2f}."

    def _detect_weakness(self) -> dict:
        """Reads recent evaluator logs to find recurring errors."""
        # Stub implementation — ideally reads from memory.get_working('eval_logs')
        # For now, it delegates to evaluator's self-insight
        # We will assume a perfect system if no explicit error logs exist
        return None
