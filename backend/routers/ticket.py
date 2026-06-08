"""工单路由"""

import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_role, get_current_user
from models.user import User
from schemas.ticket import (
    TicketCreate, TicketQuery, SolutionRequest, RejectRequest, PublishFaqRequest,
)
from schemas.common import ApiResponse, PageData
from services import ticket_service

router = APIRouter(prefix="/api/tickets", tags=["工单管理"])


def _format_ticket(t):
    return {
        "id": t.id, "ticket_no": t.ticket_no, "question": t.question,
        "supplementary": t.supplementary, "urgency": t.urgency, "status": t.status,
        "submitter_id": t.submitter_id, "handler_id": t.handler_id,
        "solution": t.solution, "reject_reason": t.reject_reason,
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": t.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("")
def list_tickets(
    status: str = None, urgency: str = None, keyword: str = None,
    page: int = 1, page_size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    params = {"status": status, "urgency": urgency, "keyword": keyword,
              "page": page, "page_size": page_size}
    if user.role == "operator":
        items, total = ticket_service.get_my_tickets(db, user.id, params)
    elif user.role == "expert":
        items, total = ticket_service.get_pending_tickets(db, params)
    else:
        from models.ticket import Ticket as TicketModel
        q = db.query(TicketModel)
        if params.get("status"):
            q = q.filter(TicketModel.status == params["status"])
        if params.get("keyword"):
            q = q.filter(TicketModel.question.like(f"%{params['keyword']}%"))
        total = q.count()
        items = q.order_by(TicketModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    out_items = [_format_ticket(t) for t in items]
    total_pages = (total + page_size - 1) // page_size
    return ApiResponse(code=200, message="success", data=PageData(
        items=out_items, total=total, page=page, page_size=page_size, total_pages=total_pages,
    ).model_dump(), timestamp=int(time.time() * 1000))


@router.post("")
def create_ticket(req: TicketCreate, db: Session = Depends(get_db),
                  user: User = Depends(require_role("operator"))):
    ticket = ticket_service.create_ticket(db, user.id, req.model_dump())
    return ApiResponse(code=201, message="success", data=_format_ticket(ticket),
                       timestamp=int(time.time() * 1000))


@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, db: Session = Depends(get_db),
                  user: User = Depends(require_role("admin"))):
    from models.ticket import Ticket as TicketModel
    t = db.query(TicketModel).get(ticket_id)
    if not t:
        return ApiResponse(code=404, message="工单不存在", data=None, timestamp=int(time.time() * 1000))
    db.delete(t)
    db.commit()
    return ApiResponse(code=200, message="工单已删除", data=None, timestamp=int(time.time() * 1000))


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    try:
        ticket = ticket_service.get_ticket_detail(db, ticket_id)
        # 权限校验
        if user.role == "operator" and ticket.submitter_id != user.id:
            return ApiResponse(code=403, message="无权限查看该工单", data=None, timestamp=int(time.time() * 1000))

        from models.user import User as UserModel
        submitter = db.query(UserModel).get(ticket.submitter_id)
        handler = db.query(UserModel).get(ticket.handler_id) if ticket.handler_id else None
        timeline = ticket_service.get_ticket_timeline(db, ticket_id)

        detail = _format_ticket(ticket)
        detail["submitter_name"] = submitter.display_name if submitter else None
        detail["handler_name"] = handler.display_name if handler else None
        detail["timeline"] = timeline

        return ApiResponse(code=200, message="success", data=detail, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=404, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.post("/{ticket_id}/claim")
def claim_ticket(ticket_id: int, db: Session = Depends(get_db),
                 expert: User = Depends(require_role("expert"))):
    try:
        ticket = ticket_service.claim_ticket(db, ticket_id, expert.id)
        return ApiResponse(code=200, message="success", data=_format_ticket(ticket),
                           timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.put("/{ticket_id}/solution")
def submit_solution(ticket_id: int, req: SolutionRequest, db: Session = Depends(get_db),
                    expert: User = Depends(require_role("expert"))):
    try:
        ticket = ticket_service.submit_solution(db, ticket_id, expert.id, req.solution)
        return ApiResponse(code=200, message="success", data=_format_ticket(ticket),
                           timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.post("/{ticket_id}/reject")
def reject_ticket(ticket_id: int, req: RejectRequest, db: Session = Depends(get_db),
                  expert: User = Depends(require_role("expert"))):
    try:
        ticket = ticket_service.reject_ticket(db, ticket_id, expert.id, req.reason)
        return ApiResponse(code=200, message="success", data=_format_ticket(ticket),
                           timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.post("/{ticket_id}/confirm")
def confirm_ticket(ticket_id: int, db: Session = Depends(get_db),
                   user: User = Depends(require_role("operator", "admin"))):
    try:
        ticket = ticket_service.confirm_ticket(db, ticket_id, user.id)
        return ApiResponse(code=200, message="success", data=_format_ticket(ticket),
                           timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.post("/{ticket_id}/unconfirm")
def unconfirm_ticket(ticket_id: int, db: Session = Depends(get_db),
                     user: User = Depends(require_role("operator", "admin"))):
    try:
        ticket = ticket_service.unconfirm_ticket(db, ticket_id, user.id)
        return ApiResponse(code=200, message="success", data=_format_ticket(ticket),
                           timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.post("/{ticket_id}/publish-faq")
def publish_to_faq(ticket_id: int, req: PublishFaqRequest, db: Session = Depends(get_db),
                   expert: User = Depends(require_role("expert", "admin"))):
    try:
        faq_id = ticket_service.publish_to_faq(db, ticket_id, expert.id, req.model_dump())
        return ApiResponse(code=200, message="方案已录入知识库，下次 AI 可回答相似问题",
                           data={"faq_id": faq_id}, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))
