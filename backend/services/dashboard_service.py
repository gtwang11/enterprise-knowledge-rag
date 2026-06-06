"""仪表盘统计服务"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.user import User
from models.faq import Faq
from models.ticket import Ticket
from models.qa_history import QaHistory


def get_operator_dashboard(db: Session, user_id: int) -> dict:
    tickets = db.query(Ticket).filter(Ticket.submitter_id == user_id)
    return {
        "pending_count": tickets.filter(Ticket.status == "pending").count(),
        "processing_count": tickets.filter(Ticket.status.in_(["processing", "pending_confirmation"])).count(),
        "completed_count": tickets.filter(Ticket.status == "completed").count(),
    }


def get_expert_dashboard(db: Session, user_id: int) -> dict:
    week_ago = datetime.utcnow() - timedelta(days=7)
    trend = []
    for i in range(7):
        day = week_ago + timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = db.query(Ticket).filter(
            Ticket.handler_id == user_id,
            Ticket.completed_at >= day,
            Ticket.completed_at < next_day,
        ).count()
        trend.append({"date": day.strftime("%m-%d"), "count": count})

    return {
        "pending_total": db.query(Ticket).filter(Ticket.status == "pending").count(),
        "my_processing": db.query(Ticket).filter(Ticket.handler_id == user_id, Ticket.status == "processing").count(),
        "my_awaiting": db.query(Ticket).filter(Ticket.handler_id == user_id, Ticket.status == "pending_confirmation").count(),
        "my_completed": db.query(Ticket).filter(Ticket.handler_id == user_id, Ticket.status == "completed").count(),
        "trend_7days": trend,
    }


def get_admin_dashboard(db: Session) -> dict:
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)

    qa_trend = []
    for i in range(7):
        day = week_ago + timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = db.query(QaHistory).filter(
            QaHistory.created_at >= day,
            QaHistory.created_at < next_day,
        ).count()
        qa_trend.append({"date": day.strftime("%m-%d"), "count": count})

    return {
        "total_users": db.query(User).filter(User.status == "active").count(),
        "active_users": db.query(User).filter(User.last_login_at >= week_ago).count(),
        "total_faqs": db.query(Faq).filter(Faq.status == "published").count(),
        "today_qa_count": db.query(QaHistory).filter(QaHistory.created_at >= today).count(),
        "ticket_stats": {
            "pending": db.query(Ticket).filter(Ticket.status == "pending").count(),
            "processing": db.query(Ticket).filter(Ticket.status == "processing").count(),
            "pending_confirmation": db.query(Ticket).filter(Ticket.status == "pending_confirmation").count(),
            "completed": db.query(Ticket).filter(Ticket.status == "completed").count(),
        },
        "qa_trend_7days": qa_trend,
    }
