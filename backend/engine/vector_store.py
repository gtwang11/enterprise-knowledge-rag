"""ChromaDB 向量存储封装 + 重试机制"""

import time

from config import (
    CHROMA_DB_PATH, CHROMA_COLLECTION_NAME,
    RAG_MAX_RETRIES, RAG_RETRY_INTERVAL_SECONDS, RAG_TOP_K,
)

_chroma_client = None


def _get_client():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _chroma_client


def get_vector_store():
    return VectorStore()


class VectorStore:
    """ChromaDB 封装，含重试机制"""

    def _retry(self, func, *args, **kwargs):
        """带重试的操作包装器"""
        for attempt in range(RAG_MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < RAG_MAX_RETRIES - 1:
                    from utils.logger import app_logger
                    app_logger.warning(f"向量库操作失败，重试第 {attempt + 1}/{RAG_MAX_RETRIES} 次: {e}")
                    time.sleep(RAG_RETRY_INTERVAL_SECONDS)
                else:
                    from utils.logger import app_logger
                    app_logger.error(f"向量库操作失败，已重试 {RAG_MAX_RETRIES} 次: {e}")
                    raise

    @property
    def collection(self):
        client = _get_client()
        return client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_faq(self, faq_id: int, question: str, answer: str, category: str, keywords: str):
        """添加 FAQ 向量"""
        text = f"{question} {category} {keywords} {answer[:200]}"
        from engine.embedding_manager import EmbeddingManager
        embedder = EmbeddingManager()
        vector = embedder.embed(text)

        self._retry(
            lambda: self.collection.add(
                ids=[str(faq_id)],
                embeddings=[vector],
                metadatas=[{
                    "faq_id": faq_id,
                    "question": question[:500],
                    "category": category,
                }],
                documents=[question],
            )
        )

    def delete_faq(self, faq_id: int):
        """删除 FAQ 向量"""
        self._retry(
            lambda: self.collection.delete(ids=[str(faq_id)])
        )

    def search(self, query_vector: list[float], k: int = None) -> list:
        """向量相似度检索，返回 [{"faq_id", "question", "similarity"}, ...]"""
        if k is None:
            k = RAG_TOP_K

        results = self._retry(
            lambda: self.collection.query(
                query_embeddings=[query_vector],
                n_results=k,
                include=["metadatas", "distances", "documents"],
            )
        )

        items = []
        if results and results.get("ids") and results["ids"][0]:
            for i, faq_id_str in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                distance = results["distances"][0][i] if results.get("distances") else 0
                # ChromaDB 返回的是距离（cosine distance），转为相似度
                similarity = 1.0 - distance

                items.append({
                    "faq_id": int(faq_id_str),
                    "question": metadata.get("question", ""),
                    "similarity": similarity,
                })

        return items
