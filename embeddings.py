# -*- coding: utf-8 -*-
"""
embeddings.py — Vector Embedding Engine
Uses Ollama's embed API for semantic vector representations.
Falls back to TF-IDF vectors if Ollama embedding model unavailable.
"""

import math
import struct
import string
import re
from collections import Counter

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 500        # characters per chunk
CHUNK_OVERLAP = 100     # overlap between chunks
SIMILARITY_THRESHOLD = 0.95  # deduplication threshold

STOP_WORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for", "of",
    "and", "or", "but", "i", "you", "he", "she", "we", "they", "do",
    "did", "does", "has", "have", "had", "be", "am", "are", "was", "were",
    "will", "would", "could", "should", "may", "might", "shall", "can",
    "not", "no", "so", "if", "as", "by", "from", "with", "this", "that",
    "these", "those", "my", "your", "his", "her", "its", "our", "their",
    "me", "him", "us", "them", "what", "which", "who", "whom", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "than", "too", "very", "just", "about", "up", "out", "then", "now",
}


class EmbeddingEngine:
    """Handles text embedding via Ollama or TF-IDF fallback."""

    def __init__(self):
        self.use_ollama = False
        self._vocab = {}  # For TF-IDF fallback
        self._doc_count = 0
        self._df = Counter()  # document frequency

        if HAS_OLLAMA:
            self._try_ollama_setup()

        if self.use_ollama:
            print("[Embeddings] Using Ollama neural embeddings")
        else:
            print("[Embeddings] Using TF-IDF fallback (run 'ollama pull nomic-embed-text' for better quality)")

    def _try_ollama_setup(self):
        """Check if embedding model is available."""
        try:
            models = ollama.list()
            model_names = [m.model for m in models.models] if models.models else []
            for name in model_names:
                if "nomic-embed" in name or "embed" in name:
                    self.use_ollama = True
                    return
            # Try to pull it
            print(f"[Embeddings] Pulling {EMBED_MODEL}...")
            ollama.pull(EMBED_MODEL)
            self.use_ollama = True
        except Exception as e:
            print(f"[Embeddings] Ollama embed not available: {e}")
            self.use_ollama = False

    # ─────────────────────────────────────────────────────────────────────────
    #  EMBEDDING GENERATION
    # ─────────────────────────────────────────────────────────────────────────
    def embed(self, text: str) -> list:
        """Generate embedding vector for text."""
        if not text or not text.strip():
            return []
        if self.use_ollama:
            return self._ollama_embed(text)
        return self._tfidf_embed(text)

    def embed_batch(self, texts: list) -> list:
        """Generate embeddings for multiple texts."""
        if self.use_ollama:
            return [self._ollama_embed(t) for t in texts if t.strip()]
        return [self._tfidf_embed(t) for t in texts if t.strip()]

    def _ollama_embed(self, text: str) -> list:
        """Get embedding from Ollama."""
        try:
            result = ollama.embed(model=EMBED_MODEL, input=text)
            if result and result.embeddings:
                return result.embeddings[0]
        except Exception as e:
            print(f"[Embeddings] Ollama embed error: {e}")
        return self._tfidf_embed(text)  # Fallback

    def _tfidf_embed(self, text: str) -> list:
        """Simple TF-IDF vector as fallback."""
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * 100

        # Update vocabulary
        unique_tokens = set(tokens)
        for t in unique_tokens:
            if t not in self._vocab:
                self._vocab[t] = len(self._vocab)
            self._df[t] += 1
        self._doc_count += 1

        # Build sparse vector, hash to fixed 256-dim
        dim = 256
        vector = [0.0] * dim
        tf = Counter(tokens)
        for token, count in tf.items():
            tf_val = count / len(tokens)
            idf_val = math.log((self._doc_count + 1) / (self._df.get(token, 0) + 1)) + 1
            idx = hash(token) % dim
            vector[idx] += tf_val * idf_val

        # Normalize
        mag = math.sqrt(sum(v * v for v in vector))
        if mag > 0:
            vector = [v / mag for v in vector]
        return vector

    def _tokenize(self, text: str) -> list:
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        tokens = text.split()
        return [t for t in tokens if t not in STOP_WORDS and len(t) > 2]

    # ─────────────────────────────────────────────────────────────────────────
    #  SIMILARITY
    # ─────────────────────────────────────────────────────────────────────────
    def cosine_similarity(self, vec1: list, vec2: list) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        if len(vec1) != len(vec2):
            return 0.0

        if HAS_NUMPY:
            a = np.array(vec1)
            b = np.array(vec2)
            dot = np.dot(a, b)
            mag = np.linalg.norm(a) * np.linalg.norm(b)
            return float(dot / mag) if mag > 0 else 0.0

        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    def is_duplicate(self, vec1: list, vec2: list, threshold: float = SIMILARITY_THRESHOLD) -> bool:
        """Check if two embeddings represent duplicate content."""
        return self.cosine_similarity(vec1, vec2) >= threshold

    # ─────────────────────────────────────────────────────────────────────────
    #  SERIALIZATION — store vectors in SQLite as BLOBs
    # ─────────────────────────────────────────────────────────────────────────
    def serialize(self, vector: list) -> bytes:
        """Convert float list to bytes for SQLite BLOB storage."""
        if not vector:
            return b""
        return struct.pack(f"{len(vector)}f", *vector)

    def deserialize(self, blob: bytes) -> list:
        """Convert bytes back to float list."""
        if not blob:
            return []
        n = len(blob) // 4  # 4 bytes per float
        return list(struct.unpack(f"{n}f", blob))

    # ─────────────────────────────────────────────────────────────────────────
    #  TEXT CHUNKING
    # ─────────────────────────────────────────────────────────────────────────
    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
        """
        Split text into semantic chunks.
        Tries to split on sentence boundaries within the chunk size.
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []

        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Overlap: keep last part of previous chunk
                words = current_chunk.split()
                overlap_words = words[-overlap // 5:] if len(words) > overlap // 5 else []
                current_chunk = " ".join(overlap_words) + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks


# ─────────────────────────────────────────────────────────────────────────────
#  Quick test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = EmbeddingEngine()

    text1 = "Machine learning is a subset of artificial intelligence that learns from data."
    text2 = "AI and ML are closely related fields in computer science."
    text3 = "The weather today is sunny with a high of 75 degrees."

    v1 = engine.embed(text1)
    v2 = engine.embed(text2)
    v3 = engine.embed(text3)

    print(f"Vector dim: {len(v1)}")
    print(f"ML vs AI similarity: {engine.cosine_similarity(v1, v2):.4f}")
    print(f"ML vs Weather similarity: {engine.cosine_similarity(v1, v3):.4f}")

    # Test chunking
    long_text = "First sentence. " * 50
    chunks = engine.chunk_text(long_text)
    print(f"\nChunked {len(long_text)} chars into {len(chunks)} chunks")

    # Test serialization
    blob = engine.serialize(v1)
    restored = engine.deserialize(blob)
    print(f"Serialization roundtrip OK: {v1[:3]} == {restored[:3]}")
