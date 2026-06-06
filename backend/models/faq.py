"""FAQ 模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from database import Base


class Faq(Base):
    __tablename__ = "faq"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    tags = Column(String(200), default=None)
    keywords = Column(String(500), default=None)
    status = Column(String(10), nullable=False, default="published", index=True)
    version = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), default=None)
    source_ticket_id = Column(Integer, ForeignKey("tickets.id"), default=None, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
