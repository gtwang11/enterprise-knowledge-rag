"""工单模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_no = Column(String(30), unique=True, nullable=False, index=True)
    question = Column(String(2000), nullable=False)
    supplementary = Column(Text, default=None)
    urgency = Column(String(10), nullable=False, default="normal", index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    handler_id = Column(Integer, ForeignKey("users.id"), default=None, index=True)
    solution = Column(Text, default=None)
    reject_reason = Column(String(500), default=None)
    confirmed_at = Column(DateTime, default=None)
    completed_at = Column(DateTime, default=None)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
