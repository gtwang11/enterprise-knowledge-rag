"""用户模型"""

from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    display_name = Column(String(50), nullable=False)
    phone = Column(String(11), unique=True, nullable=False)
    email = Column(String(100), default=None)
    department = Column(String(50), nullable=False)
    role = Column(String(10), nullable=False, default="operator")
    status = Column(String(10), nullable=False, default="active")
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, default=None)
    last_login_at = Column(DateTime, default=None)
    is_first_login = Column(Integer, nullable=False, default=1)
    password_updated_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
