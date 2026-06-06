"""FAQ 知识库服务"""

from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.faq import Faq
from utils.faq_importer import ALLOWED_CATEGORIES


def create_faq(db: Session, data: dict, user_id: int) -> Faq:
    faq = Faq(
        question=data["question"],
        answer=data["answer"],
        category=data["category"],
        tags=data.get("tags"),
        keywords=data.get("keywords"),
        created_by=user_id,
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)

    # 触发向量化
    from engine.vector_store import get_vector_store
    try:
        store = get_vector_store()
        store.add_faq(faq.id, faq.question, faq.answer, faq.category, faq.keywords or "")
    except Exception as e:
        from utils.logger import app_logger
        app_logger.error(f"FAQ新增向量化失败: faq_id={faq.id}, error={e}")

    return faq


def update_faq(db: Session, faq_id: int, data: dict, user_id: int) -> Faq:
    faq = db.query(Faq).get(faq_id)
    if not faq:
        raise ValueError("FAQ不存在")

    for field in ["question", "answer", "category", "tags", "keywords", "status"]:
        if field in data and data[field] is not None:
            setattr(faq, field, data[field])
    faq.version += 1
    faq.updated_by = user_id
    faq.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(faq)

    # 同步向量库
    from engine.vector_store import get_vector_store
    try:
        store = get_vector_store()
        store.delete_faq(faq.id)
        if faq.status == "published":
            store.add_faq(faq.id, faq.question, faq.answer, faq.category, faq.keywords or "")
    except Exception as e:
        from utils.logger import app_logger
        app_logger.error(f"FAQ修改向量化失败: faq_id={faq.id}, error={e}")

    return faq


def delete_faqs(db: Session, ids: list[int]):
    faqs = db.query(Faq).filter(Faq.id.in_(ids)).all()
    if not faqs:
        raise ValueError("未找到要删除的FAQ")

    from engine.vector_store import get_vector_store
    store = get_vector_store()

    for faq in faqs:
        try:
            store.delete_faq(faq.id)
        except Exception as e:
            from utils.logger import app_logger
            app_logger.error(f"FAQ删除向量化失败: faq_id={faq.id}, error={e}")

    db.query(Faq).filter(Faq.id.in_(ids)).delete(synchronize_session=False)
    db.commit()


def query_faqs(db: Session, params: dict) -> tuple:
    q = db.query(Faq)

    if params.get("keyword"):
        kw = f"%{params['keyword']}%"
        q = q.filter(or_(Faq.question.like(kw), Faq.keywords.like(kw)))
    if params.get("category"):
        q = q.filter(Faq.category == params["category"])
    if params.get("status"):
        q = q.filter(Faq.status == params["status"])
    if params.get("start_date"):
        q = q.filter(Faq.created_at >= params["start_date"])
    if params.get("end_date"):
        q = q.filter(Faq.created_at <= params["end_date"] + " 23:59:59")

    total = q.count()
    page = params.get("page", 1)
    page_size = params.get("page_size", 20)
    items = q.order_by(Faq.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return items, total


def bulk_import_faqs(db: Session, items: list[dict], user_id: int) -> dict:
    """先批量写入数据库，再同步向量化（带批控和重试）"""
    from config import VECTORIZE_BATCH_SIZE, VECTORIZE_BATCH_DELAY

    faq_ids = []
    for item in items:
        faq = Faq(
            question=item["question"],
            answer=item["answer"],
            category=item["category"],
            tags=item.get("tags"),
            keywords=item.get("keywords"),
            created_by=user_id,
        )
        db.add(faq)
        faq_ids.append(faq)

    db.commit()
    faq_ids = [f.id for f in faq_ids]

    # 后台线程分批向量化，带重试 + 延迟防止 Ollama 过载
    import threading
    def _vectorize_background():
        from engine.vector_store import get_vector_store
        from engine.embedding_manager import EmbeddingManager
        from database import SessionLocal
        from utils.logger import app_logger
        import time

        store = get_vector_store()
        embedder = EmbeddingManager()
        bg_db = SessionLocal()

        ok = 0
        fail = 0
        max_retries = 3
        total = len(faq_ids)

        for batch_start in range(0, total, VECTORIZE_BATCH_SIZE):
            batch = faq_ids[batch_start:batch_start + VECTORIZE_BATCH_SIZE]
            for fid in batch:
                for attempt in range(1, max_retries + 1):
                    try:
                        faq = bg_db.query(Faq).get(fid)
                        if faq:
                            store.add_faq(fid, faq.question, faq.answer, faq.category, faq.keywords or "")
                            ok += 1
                        break  # 成功则跳出重试循环
                    except Exception as e:
                        if attempt < max_retries:
                            backoff = 2 ** attempt
                            app_logger.warning(
                                f"后台向量化失败 faq_id={fid} (第{attempt}/{max_retries}次), "
                                f"{backoff}s 后重试: {type(e).__name__}: {e}"
                            )
                            time.sleep(backoff)
                        else:
                            fail += 1
                            app_logger.error(
                                f"后台向量化最终失败 faq_id={fid} (已重试{max_retries}次): "
                                f"{type(e).__name__}: {e}"
                            )
            # 批次间休息，防止 Ollama 过载
            if batch_start + VECTORIZE_BATCH_SIZE < total:
                time.sleep(VECTORIZE_BATCH_DELAY)

        bg_db.close()
        app_logger.info(f"后台向量化完成: 成功={ok} 失败={fail} 总计={total}")

    threading.Thread(target=_vectorize_background, daemon=True, name="faq-vectorizer").start()

    return {"success_count": len(faq_ids), "skip_count": 0}


def reindex_all_faqs(db: Session) -> dict:
    """后台全量重建向量索引 — 热切换，查询零中断

    流程：
    1. 从 DB 加载全部 published FAQ
    2. 后台线程写入临时集合 (faq_vectors_v2_xxx)
    3. 写入完成后原子切换活跃集合
    4. 删除旧集合
    """
    from engine.vector_store import get_vector_store
    from utils.logger import app_logger

    faqs = db.query(Faq).filter(Faq.status == "published").all()
    if not faqs:
        return {"success": False, "message": "没有已发布的 FAQ，无需重建"}

    store = get_vector_store()
    result = store.rebuild_index_background(faqs)
    app_logger.info(f"全量重建索引已启动: {result}")
    return result
