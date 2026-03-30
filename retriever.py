# -*- coding: utf-8 -*-
"""
retriever.py — 3-Pass Retrieval Pipeline
  Pass 1: Broad fetch — top 20 chunks by embedding similarity
  Pass 2: Rerank — LLM scores top 5 by relevance
  Pass 3: Context assembly — format with citations
"""

import json
import re
from memory import Memory

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False


class Retriever:
    """
    Retrieval-Augmented Generation pipeline.
    Fetches from all memory types, reranks, and assembles context with citations.
    """

    def __init__(self, memory: Memory, model: str = None):
        self.memory = memory
        self.model = model  # LLM model name for reranking

    # ─────────────────────────────────────────────────────────────────────────
    #  MAIN ENTRY
    # ─────────────────────────────────────────────────────────────────────────
    def retrieve(self, query: str, top_k: int = 5) -> dict:
        """
        Full 3-pass retrieval pipeline.
        Returns: {
            "context": formatted string for the LLM,
            "citations": [{"id", "url", "topic", "similarity"}],
            "chunk_count": int,
            "has_context": bool,
            "procedural": optional procedure match,
            "profile": user profile summary,
            "episodes": relevant past conversations,
        }
        """
        result = {
            "context": "",
            "citations": [],
            "chunk_count": 0,
            "has_context": False,
            "procedural": None,
            "profile": "",
            "episodes": [],
        }

        # ── Pass 1: Broad semantic fetch ─────────────────────────────────────
        raw_chunks = self.memory.search_semantic(query, limit=20)

        # ── Pass 2: Rerank top chunks ────────────────────────────────────────
        if raw_chunks:
            reranked = self._rerank(query, raw_chunks, top_k=top_k)
        else:
            reranked = []

        # ── Pass 3: Assemble context with citations ──────────────────────────
        if reranked:
            result["context"] = self._assemble_context(query, reranked)
            result["citations"] = [
                {
                    "id": c["id"],
                    "url": c["url"],
                    "topic": c["topic"],
                    "similarity": round(c.get("similarity", 0), 3),
                    "quality": round(c.get("source_quality", 0.5), 2),
                }
                for c in reranked
            ]
            result["chunk_count"] = len(reranked)
            result["has_context"] = True

        # ── Procedural memory check ──────────────────────────────────────────
        procedure = self.memory.find_procedure(query)
        if procedure:
            result["procedural"] = procedure

        # ── Profile context ──────────────────────────────────────────────────
        result["profile"] = self.memory.get_profile_summary()

        # ── Relevant past conversations ──────────────────────────────────────
        episodes = self.memory.search_episodes(query, limit=3)
        if episodes:
            result["episodes"] = episodes

        return result

    # ─────────────────────────────────────────────────────────────────────────
    #  PASS 2: RERANK
    # ─────────────────────────────────────────────────────────────────────────
    def _rerank(self, query: str, chunks: list, top_k: int = 5) -> list:
        """
        Rerank chunks by relevance to query.
        Uses LLM if available, otherwise uses heuristic scoring.
        """
        if len(chunks) <= top_k:
            return chunks

        # Try LLM reranking
        if self.model and HAS_OLLAMA:
            try:
                return self._llm_rerank(query, chunks, top_k)
            except Exception as e:
                print(f"[Retriever] LLM rerank failed: {e}, using heuristic")

        # Heuristic reranking: combine similarity, quality, and freshness
        return self._heuristic_rerank(query, chunks, top_k)

    def _heuristic_rerank(self, query: str, chunks: list, top_k: int) -> list:
        """Score chunks by similarity * quality * recency."""
        query_words = set(query.lower().split())

        for chunk in chunks:
            sim = chunk.get("similarity", 0)
            qual = chunk.get("source_quality", 0.5)

            # Word overlap bonus
            chunk_words = set(chunk.get("chunk_text", "").lower().split())
            overlap = len(query_words & chunk_words) / max(len(query_words), 1)

            # Combined score
            chunk["rerank_score"] = (sim * 0.5) + (qual * 0.3) + (overlap * 0.2)

        chunks.sort(key=lambda c: c.get("rerank_score", 0), reverse=True)
        return chunks[:top_k]

    def _llm_rerank(self, query: str, chunks: list, top_k: int) -> list:
        """Use the LLM to score chunk relevance."""
        # Build compact chunk summaries for the LLM
        chunk_summaries = []
        for i, c in enumerate(chunks[:10]):  # Cap at 10 to keep prompt small
            text = c.get("chunk_text", "")[:300]
            chunk_summaries.append(f"[{i}] {text}")

        prompt = (
            f"Given the user query: \"{query}\"\n\n"
            f"Rate each chunk's relevance (0-10). Return ONLY a JSON array of "
            f"[chunk_index, score] pairs, sorted by score descending.\n\n"
            + "\n".join(chunk_summaries)
        )

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0, "num_predict": 200}
        )

        reply = response.message.content.strip()

        # Parse scores
        try:
            # Try to find JSON array in response
            match = re.search(r'\[.*\]', reply, re.DOTALL)
            if match:
                scores = json.loads(match.group())
                # Reorder chunks by LLM scores
                scored_chunks = []
                for idx, score in scores[:top_k]:
                    if 0 <= idx < len(chunks):
                        chunks[idx]["rerank_score"] = score
                        scored_chunks.append(chunks[idx])
                if scored_chunks:
                    return scored_chunks
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        # Fallback to heuristic
        return self._heuristic_rerank(query, chunks, top_k)

    # ─────────────────────────────────────────────────────────────────────────
    #  PASS 3: CONTEXT ASSEMBLY
    # ─────────────────────────────────────────────────────────────────────────
    def _assemble_context(self, query: str, chunks: list) -> str:
        """Format retrieved chunks with citations for the LLM."""
        sections = []

        for i, chunk in enumerate(chunks):
            cite_id = i + 1
            url = chunk.get("url", "unknown")
            topic = chunk.get("topic", "")
            text = chunk.get("chunk_text", "")[:1500]
            quality = chunk.get("source_quality", 0.5)
            similarity = chunk.get("similarity", 0)

            sections.append(
                f"[Citation {cite_id}] Source: {url}\n"
                f"Topic: {topic} | Quality: {quality:.1f} | Relevance: {similarity:.2f}\n"
                f"{text}"
            )

        header = (
            "=== RETRIEVED KNOWLEDGE ===\n"
            "Use these sources to answer. Cite sources by number [1], [2] etc.\n"
            "If sources conflict, prefer higher quality scores.\n\n"
        )
        footer = "\n=== END KNOWLEDGE ===\n"

        return header + "\n\n---\n\n".join(sections) + footer

    def format_citations_for_user(self, citations: list) -> str:
        """Format citations for display to the user."""
        if not citations:
            return ""
        lines = ["\nSources:"]
        for i, c in enumerate(citations):
            lines.append(f"  [{i+1}] {c['topic']} — {c['url']}")
        return "\n".join(lines)
