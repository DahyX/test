# -*- coding: utf-8 -*-
"""
workflow_result_interpreter.py — Synthesis & Normalization
Compresses massive API JSON responses back into conversational text so Jarvis doesn't overload its token window.
"""

from tools.activepieces_models import ToolExecutionResult

class WorkflowResultInterpreter:
    def __init__(self):
        pass

    def interpret(self, execution_result: ToolExecutionResult) -> ToolExecutionResult:
        """
        Reads raw JSON responses and translates them into a single-sentence conversational summary.
        """
        if not execution_result.success:
            execution_result.normalized_result = f"Failed to execute backend action '{execution_result.action_name}': {execution_result.error_message}"
            return execution_result
            
        # TODO: If raw JSON is massive, pass to a tiny LLM for extraction
        # Placeholder heuristic
        raw = execution_result.raw_result
        if "mock_response" in raw:
            execution_result.normalized_result = f"I successfully triggered the {execution_result.action_name} automation workflow."
        else:
            execution_result.normalized_result = f"The {execution_result.action_name} executed. Backend returned success data."
            
        return execution_result
