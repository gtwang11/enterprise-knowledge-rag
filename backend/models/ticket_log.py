"""工单日志模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from database import Base


class TicketLog(Base):
    __tablename__ = "ticket_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(30), nullable=False)
    from_status = Column(String(20), default=None)
    to_status = Column(String(20), default=None)
    comment = Column(Text, default=None)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
