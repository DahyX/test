# -*- coding: utf-8 -*-
"""
test_phase2.py — Validates the V6 sandboxed self-improvement pipeline.
"""

from action.action_router import ActionRouter
from core.runtime_state import ActionCandidate

def run_test():
    print("=== Jarvis V6 Phase 2 Validation ===")
    
    router = ActionRouter()
    
    # Simulate the DecisionEngine deciding to use the self_improve tool
    test_action = ActionCandidate(
        tool_name="self_improve",
        params={
            "target_file": "reasoning/intent_analyzer.py",
            "issue_description": "Add a fast-path heuristic for the word 'weather' to automatically set the intent to 'check_weather_forecast'."
        },
        expected_result="The intent analyzer safely patched and recompiled.",
        risk_level="medium"
    )
    
    # Execute the action
    print("\n[Test] Dispatching self_improve action to ActionRouter...")
    result = router.execute(test_action)
    
    print("\n=== Test Final Output ===")
    print(result)

if __name__ == "__main__":
    run_test()
