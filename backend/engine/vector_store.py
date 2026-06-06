"""ChromaDB 向量存储封装 + 重试机制 + 线程安全 + 原子热切换"""

import os
import time
import threading

from config import (
    CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, DATA_DIR,
    RAG_MAX_RETRIES, RAG_RETRY_INTERVAL_SECONDS, RAG_TOP_K,
)

_chroma_client = None
_client_lock = threading.Lock()

# 活跃集合名持久化文件
_COLLECTION_NAME_FILE = os.path.join(DATA_DIR, ".active_collection")


def _load_active_collection_name():
    """从持久化文件加载活跃集合名，不存在则返回默认值"""
    try:
        if os.path.exists(_COLLECTION_NAME_FILE):
            with open(_COLLECTION_NAME_FILE, "r", encoding="utf-8") as f:
                saved = f.read().strip()
            # 验证该集合是否真实存在
            client = _get_client()
            try:
                client.get_collection(saved)
                return saved
            except Exception:
                pass  # 集合不存在，回退到默认
    except Exception:
        pass
    return CHROMA_COLLECTION_NAME


def _save_active_collection_name(name: str):
    """持久化当前活跃集合名"""
    try:
        with open(_COLLECTION_NAME_FILE, "w", encoding="utf-8") as f:
            f.write(name)
    except Exception:
        pass  # 持久化失败不应影响主流程


# 活跃集合名 — 原子热切换：reindex 先写入临时集合，完成后一键指向新集合
_active_collection_name = _load_active_collection_name()
_collection_name_lock = threading.RLock()

# 重建状态（供 /api/faq/reindex/status 查询）
_reindex_status = {
    "running": False,
    "total": 0,
    "indexed": 0,
    "failed": 0,
    "phase": "idle",  # idle | building | swapping | done | error
    "error": None,
}


def get_reindex_status() -> dict:
    """查询当前重建状态"""
    with _collection_name_lock:
        return dict(_reindex_status)


def _get_client():
    global _chroma_client
    if _chroma_client is None:
        with _client_lock:
            if _chroma_client is None:  # double-checked locking
                import chromadb
                _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _chroma_client


def get_vector_store():
    return VectorStore()


class VectorStore:
    """ChromaDB 封装，含重试机制 + 活跃集合热切换"""

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
        with _collection_name_lock:
            name = _active_collection_name
        return client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def _get_collection_by_name(self, name: str):
        """获取指定名称的 collection"""
        client = _get_client()
        return client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_faq(self, faq_id: int, question: str, answer: str, category: str, keywords: str):
        """添加 FAQ 向量（写入活跃集合）"""
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
        """删除 FAQ 向量（从活跃集合）"""
        self._retry(
            lambda: self.collection.delete(ids=[str(faq_id)])
        )

    def search(self, query_vector: list[float], k: int = None) -> list:
        """向量相似度检索 — 始终从活跃集合查询，不受重建影响"""
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
                similarity = 1.0 - distance

                items.append({
                    "faq_id": int(faq_id_str),
                    "question": metadata.get("question", ""),
                    "similarity": similarity,
                })

        return items

    def rebuild_index_background(self, faqs: list) -> dict:
        """后台全量重建索引 — 写入临时集合，完成后原子切换，零停机

        faqs: list of Faq ORM objects (需含 id, question, answer, category, keywords)
        返回: {"thread_id": str, "message": str}
        """
        global _reindex_status

        with _collection_name_lock:
            if _reindex_status["running"]:
                return {"success": False, "message": "已有重建任务正在运行，请等待完成后再试"}
            _reindex_status.update({
                "running": True, "total": len(faqs), "indexed": 0,
                "failed": 0, "phase": "building", "error": None,
            })

        import uuid
        thread_id = str(uuid.uuid4())[:8]

        def _rebuild():
            global _active_collection_name, _reindex_status
            from engine.embedding_manager import EmbeddingManager
            from utils.logger import app_logger

            embedder = EmbeddingManager()
            client = _get_client()
            temp_name = f"{CHROMA_COLLECTION_NAME}_v2_{thread_id}"

            try:
                # Phase 1: 写入临时集合
                temp_col = client.get_or_create_collection(
                    name=temp_name,
                    metadata={"hnsw:space": "cosine"},
                )

                ok = 0
                fail = 0
                batch_size = 50
                total = len(faqs)

                for i, faq in enumerate(faqs):
                    try:
                        text = f"{faq.question} {faq.category} {faq.keywords or ''} {faq.answer[:200]}"
                        vector = embedder.embed(text)
                        temp_col.add(
                            ids=[str(faq.id)],
                            embeddings=[vector],
                            metadatas=[{
                                "faq_id": faq.id,
                                "question": faq.question[:500],
                                "category": faq.category,
                            }],
                            documents=[faq.question],
                        )
                        ok += 1
                    except Exception as e:
                        fail += 1
                        app_logger.error(f"重建索引失败 faq_id={faq.id}: {type(e).__name__}: {e}")

                    # 更新进度
                    with _collection_name_lock:
                        _reindex_status["indexed"] = ok
                        _reindex_status["failed"] = fail

                    # 批次间休息
                    if (i + 1) % batch_size == 0:
                        time.sleep(2)

                app_logger.info(f"临时集合构建完成: {temp_name} 成功={ok} 失败={fail}")

                # Phase 2: 原子切换
                with _collection_name_lock:
                    _reindex_status["phase"] = "swapping"
                    _reindex_status["indexed"] = ok
                    _reindex_status["failed"] = fail

                old_name = _active_collection_name
                with _collection_name_lock:
                    _active_collection_name = temp_name
                _save_active_collection_name(temp_name)  # 持久化，重启不丢失
                app_logger.info(f"活跃集合已切换: {old_name} → {temp_name}")

                # Phase 3: 删除旧集合（异步清理，即使失败也不影响查询）
                try:
                    client.delete_collection(name=old_name)
                    app_logger.info(f"旧集合已删除: {old_name}")
                except Exception as e:
                    app_logger.warning(f"删除旧集合失败（不影响查询）: {e}")

                with _collection_name_lock:
                    _reindex_status.update({
                        "running": False, "phase": "done",
                        "indexed": ok, "failed": fail,
                    })

            except Exception as e:
                app_logger.error(f"后台重建索引失败: {e}")
                # 清理失败的临时集合
                try:
                    client.delete_collection(name=temp_name)
                except Exception:
                    pass
                with _collection_name_lock:
                    _reindex_status.update({
                        "running": False, "phase": "error",
                        "error": str(e),
                    })

        threading.Thread(
            target=_rebuild, daemon=True,
            name=f"reindex-{thread_id}",
        ).start()

        return {
            "success": True,
            "thread_id": thread_id,
            "total": len(faqs),
            "message": f"后台重建已启动 (thread={thread_id})，预计 {len(faqs) * 0.5:.0f}s 完成，期间查询不受影响",
        }
