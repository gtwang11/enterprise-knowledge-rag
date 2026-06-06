"""问答服务：编排 RAG 管线"""

import time

from sqlalchemy.orm import Session

from models.qa_history import QaHistory
from engine.rag_pipeline import RAGPipeline

_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


def ask_question(db: Session, user_id: int, question: str) -> dict:
    """处理问答请求"""
    pipeline = get_rag_pipeline()
    start_time = time.time()

    result = pipeline.execute(question)

    processing_time_ms = int((time.time() - start_time) * 1000)

    # 记录问答历史
    record = QaHistory(
        user_id=user_id,
        question=question,
        answer=result.get("answer"),
        has_answer=1 if result["has_answer"] else 0,
        similarity_score=result.get("similarity", 0.0),
        matched_faq_ids=",".join(str(r["faq_id"]) for r in result.get("references", [])),
        processing_time_ms=processing_time_ms,
    )
    db.add(record)
    db.commit()

    # 每个用户只保留最近20条
    old = db.query(QaHistory).filter(QaHistory.user_id == user_id)\
        .order_by(QaHistory.created_at.desc()).offset(20).all()
    for r in old:
        db.delete(r)
    db.commit()

    return {
        "has_answer": result["has_answer"],
        "answer": result.get("answer"),
        "similarity": result.get("similarity", 0.0),
        "references": result.get("references", []),
        "message": result.get("message"),
    }


def get_history(db: Session, user_id: int, params: dict) -> tuple:
    q = db.query(QaHistory).filter(QaHistory.user_id == user_id)

    if params.get("start_date"):
        q = q.filter(QaHistory.created_at >= params["start_date"])
    if params.get("end_date"):
        q = q.filter(QaHistory.created_at <= params["end_date"] + " 23:59:59")

    total = q.count()
    page = params.get("page", 1)
    page_size = params.get("page_size", 20)
    items = q.order_by(QaHistory.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return items, total
