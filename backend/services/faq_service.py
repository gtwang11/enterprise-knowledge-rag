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
    """先写入数据库，后台异步向量化"""
    faq_ids = []
    # 批量插入，只 commit 一次
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
        faq_ids.append(faq)  # 暂存对象引用

    db.commit()
    # commit 后再取 id
    faq_ids = [f.id for f in faq_ids]

    # 后台线程异步向量化
    import threading
    def _vectorize_background():
        from engine.vector_store import get_vector_store
        from database import SessionLocal
        store = get_vector_store()
        bg_db = SessionLocal()
        ok = 0
        for fid in faq_ids:
            try:
                faq = bg_db.query(Faq).get(fid)
                if faq:
                    store.add_faq(fid, faq.question, faq.answer, faq.category, faq.keywords or "")
                    ok += 1
            except Exception as e:
                from utils.logger import app_logger
                app_logger.error(f"后台向量化失败 faq_id={fid}: {e}")
        bg_db.close()
        from utils.logger import app_logger
        app_logger.info(f"后台向量化完成: {ok}/{len(faq_ids)}")

    threading.Thread(target=_vectorize_background, daemon=True).start()

    return {"success_count": len(faq_ids), "skip_count": 0}
