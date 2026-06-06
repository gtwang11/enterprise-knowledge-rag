"""操作日志模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from database import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    target_type = Column(String(30), default=None)
    target_id = Column(Integer, default=None)
    detail = Column(Text, default=None)
    ip_address = Column(String(45), default=None)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
