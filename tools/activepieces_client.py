# -*- coding: utf-8 -*-
"""
activepieces_client.py — Network Transport
Pure HTTP/API Wrapper for triggering backend webhooks. Does NOT handle reasoning.
"""

import urllib.request
import urllib.error
import urllib.parse
import json
from typing import Dict, Any, Tuple
from integrations.activepieces.config import ActivepiecesConfig

class ActivepiecesClient:
    def __init__(self, config: ActivepiecesConfig):
        self.config = config

    def execute_workflow(self, workflow_id: str, payload: Dict[str, Any]) -> Tuple[bool, Any, str]:
        """
        Submits the POST request safely using standard library urllib.
        Returns: (success_bool, raw_response, error_msg)
        """
        url = f"{self.config.api_url}/webhooks/{workflow_id}"
        
        # Safe URL parsing 
        try:
            req = urllib.request.Request(url, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("Authorization", f"Bearer {self.config.api_token}")
            
            data = json.dumps(payload).encode("utf-8")
            
            # Simulated Execution Placeholder
            if self.config.api_token == "mock-token-fallback":
                print(f"[AP Client Mock] Firing Workflow {workflow_id} to {url}")
                return True, {"mock_response": "Action dispatched successfully to Activepieces."}, ""
            
            with urllib.request.urlopen(req, data=data, timeout=self.config.default_timeout_ms / 1000) as response:
                result = json.loads(response.read().decode())
                return True, result, ""
                
        except Exception as e:
            return False, None, f"Network/Client Error contacting Activepieces backend: {e}"
