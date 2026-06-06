"""Embedding 管理：调用 Ollama nomic-embed-text"""

import requests

from config import OLLAMA_BASE_URL, EMBEDDING_MODEL, EMBEDDING_DIMENSION, LLM_TIMEOUT_SECONDS


class EmbeddingManager:
    """Embedding 向量化"""

    def embed(self, text: str) -> list[float]:
        """将文本转为 768 维向量，失败时抛出异常而非返回零向量"""
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=LLM_TIMEOUT_SECONDS,
            proxies={"http": None, "https": None},
        )
        resp.raise_for_status()
        data = resp.json()
        embedding = data.get("embedding", [])
        if len(embedding) != EMBEDDING_DIMENSION:
            if len(embedding) < EMBEDDING_DIMENSION:
                embedding += [0.0] * (EMBEDDING_DIMENSION - len(embedding))
            else:
                embedding = embedding[:EMBEDDING_DIMENSION]
        return embedding
