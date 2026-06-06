"""问答路由"""

import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_role
from models.user import User
from schemas.qa import AskRequest, QaHistoryQuery
from schemas.common import ApiResponse, PageData
from services import qa_service

router = APIRouter(prefix="/api/qa", tags=["智能问答"])


@router.post("/ask")
def ask(req: AskRequest, db: Session = Depends(get_db),
        user: User = Depends(require_role("operator", "admin", "expert"))):
    result = qa_service.ask_question(db, user.id, req.question)
    return ApiResponse(code=200, message="success", data=result,
                       timestamp=int(time.time() * 1000))


@router.get("/history")
def history(
    start_date: str = None, end_date: str = None,
    page: int = 1, page_size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("operator", "admin", "expert")),
):
    params = {"start_date": start_date, "end_date": end_date,
              "page": page, "page_size": page_size}
    items, total = qa_service.get_history(db, user.id, params)
    from schemas.qa import QaHistoryOut
    out_items = [QaHistoryOut(
        id=h.id, question=h.question, answer=h.answer,
        has_answer=bool(h.has_answer), similarity_score=h.similarity_score,
        processing_time_ms=h.processing_time_ms,
        created_at=h.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    ) for h in items]
    total_pages = (total + page_size - 1) // page_size
    return ApiResponse(code=200, message="success", data=PageData(
        items=[o.model_dump() for o in out_items], total=total,
        page=page, page_size=page_size, total_pages=total_pages,
    ).model_dump(), timestamp=int(time.time() * 1000))
