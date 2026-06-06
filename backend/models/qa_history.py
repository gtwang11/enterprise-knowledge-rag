"""问答历史模型"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, func
from database import Base


class QaHistory(Base):
    __tablename__ = "qa_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question = Column(String(2000), nullable=False)
    answer = Column(Text, default=None)
    has_answer = Column(Integer, nullable=False, default=0)
    similarity_score = Column(Float, default=None)
    matched_faq_ids = Column(String(200), default=None)
    processing_time_ms = Column(Integer, nullable=False)
    created_ticket_id = Column(Integer, ForeignKey("tickets.id"), default=None)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
