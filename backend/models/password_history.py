"""密码历史模型"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from database import Base


class PasswordHistory(Base):
    __tablename__ = "password_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
