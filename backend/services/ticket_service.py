"""工单服务：状态机驱动"""

from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.ticket import Ticket
from models.ticket_log import TicketLog
from utils.ticket_no_generator import generate_ticket_no

# 状态转移规则
ALLOWED_TRANSITIONS = {
    "pending": ["processing", "closed"],
    "processing": ["pending_confirmation", "pending", "closed"],
    "pending_confirmation": ["completed", "processing", "closed"],
    "completed": ["closed"],
    "closed": [],
}


def _validate_transition(from_status: str, to_status: str):
    if to_status not in ALLOWED_TRANSITIONS.get(from_status, []):
        raise ValueError(f"不允许从 {from_status} 转移到 {to_status}")


def _log(db: Session, ticket_id: int, operator_id: int, action: str,
         from_status: str = None, to_status: str = None, comment: str = None):
    db.add(TicketLog(
        ticket_id=ticket_id,
        operator_id=operator_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        comment=comment,
    ))


def create_ticket(db: Session, user_id: int, data: dict) -> Ticket:
    ticket = Ticket(
        ticket_no=generate_ticket_no(),
        question=data["question"],
        supplementary=data.get("supplementary"),
        urgency=data.get("urgency", "normal"),
        submitter_id=user_id,
    )
    db.add(ticket)
    db.flush()
    _log(db, ticket.id, user_id, "submit", to_status="pending")
    db.commit()
    db.refresh(ticket)
    return ticket


def get_my_tickets(db: Session, user_id: int, params: dict) -> tuple:
    q = db.query(Ticket).filter(Ticket.submitter_id == user_id)
    if params.get("status"):
        q = q.filter(Ticket.status == params["status"])
    total = q.count()
    page = params.get("page", 1)
    page_size = params.get("page_size", 20)
    items = q.order_by(Ticket.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_pending_tickets(db: Session, params: dict) -> tuple:
    q = db.query(Ticket).filter(or_(
        Ticket.status == "pending",
        Ticket.status == "processing",
        Ticket.status == "pending_confirmation",
    ))
    if params.get("urgency"):
        q = q.filter(Ticket.urgency == params["urgency"])
    if params.get("status"):
        q = q.filter(Ticket.status == params["status"])
    if params.get("keyword"):
        q = q.filter(Ticket.question.like(f"%{params['keyword']}%"))
    total = q.count()
    page = params.get("page", 1)
    page_size = params.get("page_size", 20)
    items = q.order_by(
        Ticket.urgency.desc(),
        Ticket.created_at.asc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_ticket_detail(db: Session, ticket_id: int) -> Ticket:
    ticket = db.query(Ticket).get(ticket_id)
    if not ticket:
        raise ValueError("工单不存在")
    return ticket


def get_ticket_timeline(db: Session, ticket_id: int) -> list:
    logs = db.query(TicketLog).filter(
        TicketLog.ticket_id == ticket_id
    ).order_by(TicketLog.created_at.asc()).all()

    from models.user import User
    timeline = []
    for log in logs:
        user = db.query(User).get(log.operator_id)
        timeline.append({
            "action": log.action,
            "from_status": log.from_status,
            "to_status": log.to_status,
            "comment": log.comment,
            "operator_name": user.display_name if user else "未知",
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return timeline


def claim_ticket(db: Session, ticket_id: int, expert_id: int) -> Ticket:
    ticket = get_ticket_detail(db, ticket_id)
    if ticket.status != "pending":
        raise ValueError("该工单已被领取或已处理")
    if ticket.handler_id:
        raise ValueError("该工单已被其他专家领取")

    _validate_transition(ticket.status, "processing")
    _log(db, ticket_id, expert_id, "claim", from_status=ticket.status, to_status="processing")

    ticket.status = "processing"
    ticket.handler_id = expert_id
    ticket.assigned_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


def submit_solution(db: Session, ticket_id: int, expert_id: int, solution: str) -> Ticket:
    ticket = get_ticket_detail(db, ticket_id)
    if ticket.handler_id != expert_id:
        raise ValueError("您不是该工单的处理人")
    if ticket.status != "processing":
        raise ValueError("工单状态不正确")

    _validate_transition(ticket.status, "pending_confirmation")
    _log(db, ticket_id, expert_id, "solution", from_status=ticket.status, to_status="pending_confirmation")

    ticket.solution = solution
    ticket.status = "pending_confirmation"
    db.commit()
    db.refresh(ticket)
    return ticket


def reject_ticket(db: Session, ticket_id: int, expert_id: int, reason: str) -> Ticket:
    ticket = get_ticket_detail(db, ticket_id)
    if ticket.handler_id != expert_id:
        raise ValueError("您不是该工单的处理人")
    if ticket.status != "processing":
        raise ValueError("工单状态不正确")

    _validate_transition(ticket.status, "pending")
    _log(db, ticket_id, expert_id, "reject", from_status=ticket.status, to_status="pending", comment=reason)

    ticket.status = "pending"
    ticket.handler_id = None
    ticket.reject_reason = reason
    db.commit()
    db.refresh(ticket)
    return ticket


def confirm_ticket(db: Session, ticket_id: int, operator_id: int) -> Ticket:
    ticket = get_ticket_detail(db, ticket_id)
    if ticket.submitter_id != operator_id:
        raise ValueError("您不是该工单的提交人")
    if ticket.status != "pending_confirmation":
        raise ValueError("工单状态不正确")

    _validate_transition(ticket.status, "completed")
    _log(db, ticket_id, operator_id, "confirm", from_status=ticket.status, to_status="completed")

    ticket.status = "completed"
    ticket.confirmed_at = datetime.utcnow()
    ticket.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


def unconfirm_ticket(db: Session, ticket_id: int, operator_id: int) -> Ticket:
    ticket = get_ticket_detail(db, ticket_id)
    if ticket.submitter_id != operator_id:
        raise ValueError("您不是该工单的提交人")
    if ticket.status != "pending_confirmation":
        raise ValueError("工单状态不正确")

    _validate_transition(ticket.status, "processing")
    _log(db, ticket_id, operator_id, "unconfirm",
         from_status=ticket.status, to_status="processing",
         comment="报障人反馈未解决，需重新处理")

    ticket.status = "processing"
    db.commit()
    db.refresh(ticket)
    return ticket


def publish_to_faq(db: Session, ticket_id: int, expert_id: int, data: dict) -> int:
    """将工单方案录入知识库，返回新 FAQ ID"""
    ticket = get_ticket_detail(db, ticket_id)
    if ticket.status != "completed":
        raise ValueError("工单未完成，不能录入知识库")

    from models.faq import Faq

    # 检查重复
    existing = db.query(Faq).filter(Faq.question == data["question"]).first()
    if existing:
        if not data.get("overwrite"):
            raise ValueError(f"该问题已在知识库中(Faq#{existing.id})，是否覆盖？")
        existing.answer = data["answer"]
        existing.version += 1
        db.commit()
        faq_id = existing.id
    else:
        faq = Faq(
            question=data["question"],
            answer=data["answer"],
            category=data.get("category", "工单转换"),
            created_by=expert_id,
            source_ticket_id=ticket_id,
        )
        db.add(faq)
        db.flush()
        faq_id = faq.id

    db.commit()

    # 同步向量库
    from engine.vector_store import get_vector_store
    try:
        store = get_vector_store()
        if existing:
            store.delete_faq(faq_id)
        store.add_faq(faq_id, data["question"], data["answer"], data.get("category", "工单转换"), "")
    except Exception as e:
        from utils.logger import app_logger
        app_logger.error(f"工单转FAQ向量化失败: faq_id={faq_id}, error={e}")

    _log(db, ticket_id, expert_id, "publish_faq", comment=f"录入知识库 Faq#{faq_id}")
    return faq_id
