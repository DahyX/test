# -*- coding: utf-8 -*-
"""
source_permissions.py — Static Permission Matrix
Maps explicitly defined request scopes to allowed/denied action vectors.
"""

from typing import Dict, Any

class SourcePermissionsPolicy:
    """Hardcoded safe defaults for system routing."""
    
    def __init__(self):
        # The ultimate source of truth for routing boundary fences
        self.scope_matrix: Dict[str, Dict[str, Any]] = {
            "local_status": {
                "allowed_sources": ["change_history", "session_log"],
                "forbidden_sources": ["web_search", "semantic_search", "external_api"],
                "requires_web": False,
                "requires_local_state": True,
                "requires_tools": False
            },
            "local_history": {
                "allowed_sources": ["improvement_history", "change_history"],
                "forbidden_sources": ["web_search", "semantic_search", "codebase"],
                "requires_web": False,
                "requires_local_state": True,
                "requires_tools": False
            },
            "repo_code_question": {
                "allowed_sources": ["codebase", "change_history"],
                "forbidden_sources": ["web_search"],
                "requires_web": False,
                "requires_local_state": True,
                "requires_tools": True  # e.g., view_file or grep
            },
            "web_research": {
                "allowed_sources": ["web_search", "semantic_search"],
                "forbidden_sources": [],
                "requires_web": True,
                "requires_local_state": False,
                "requires_tools": True
            },
            "self_improvement_request": {
                "allowed_sources": ["codebase", "change_history"],
                "forbidden_sources": ["web_search"],
                "requires_web": False,
                "requires_local_state": True,
                "requires_tools": True
            },
            "chat": {
                "allowed_sources": ["semantic_search"],
                "forbidden_sources": ["web_search"],
                "requires_web": False,
                "requires_local_state": False,
                "requires_tools": False
            }
        }

    def get_policy(self, request_scope: str) -> Dict[str, Any]:
        """Returns the rigorous permission map, defaulting to strict safe-chat."""
        return self.scope_matrix.get(request_scope, self.scope_matrix["chat"])
