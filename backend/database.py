"""SQLAlchemy 引擎和会话工厂"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DB_PATH

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)

# Enable WAL mode for true concurrent reads
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库：创建所有表"""
    from models.user import User
    from models.password_history import PasswordHistory
    from models.token_blacklist import TokenBlacklist
    from models.faq import Faq
    from models.ticket import Ticket
    from models.ticket_log import TicketLog
    from models.qa_history import QaHistory
    from models.operation_log import OperationLog
    from models.system_config import SystemConfig

    Base.metadata.create_all(bind=engine)
