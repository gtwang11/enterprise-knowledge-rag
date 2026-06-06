"""令牌黑名单模型"""

from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token_jti = Column(String(64), unique=True, nullable=False, index=True)
    expired_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
