# -*- coding: utf-8 -*-
"""
model_router.py — Jarvis V5 Dynamic Model Orchestration
Routes tasks to different local models depending on workload and speed needs.
"""

class ModelRouter:
    def __init__(self, primary="llama3:8b", fast="phi3:mini", embeddings="nomic-embed-text"):
        self.primary_model = primary
        self.fast_model = fast
        self.embedding_model = embeddings
        
    def select_model(self, task_type: str) -> str:
        """
        Return the best model name for a given task type.
        """
        task_type = task_type.lower()
        if task_type in ("classification", "routing", "reasoning", "fast_summary"):
            # Small, fast model for logical orchestration
            return self.fast_model
            
        elif task_type in ("chat", "research", "generation", "planning"):
            # Strong reasoning and language model
            return self.primary_model
            
        elif task_type in ("coding", "self_improve", "patch_generation"):
            # Could fall back to a specific coding model like codellama or just use primary
            return self.primary_model
            
        elif task_type == "embeddings":
            return self.embedding_model
            
        # Default fallback
        return self.primary_model
