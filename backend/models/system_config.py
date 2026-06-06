"""系统配置模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    description = Column(String(200), default=None)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
