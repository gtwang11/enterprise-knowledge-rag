"""账号管理服务"""

from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.user import User
from models.password_history import PasswordHistory
from utils.security import hash_password, generate_random_password
import config


def create_user(db: Session, data: dict) -> User:
    """创建账号"""
    if db.query(User).filter(User.username == data["username"]).first():
        raise ValueError("账号名已存在")

    password = config.DEFAULT_INITIAL_PASSWORD

    user = User(
        username=data["username"],
        password_hash=hash_password(password),
        display_name=data["display_name"],
        phone=data["phone"],
        email=data.get("email"),
        department=data["department"],
        role=data["role"],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 记录初始密码（通过异常传递回去，实际生产中应通过安全渠道发送）
    user._initial_password = password
    return user


def query_users(db: Session, params: dict) -> tuple:
    """多条件查询账号"""
    q = db.query(User)

    if params.get("username"):
        q = q.filter(User.username.like(f"%{params['username']}%"))
    if params.get("display_name"):
        q = q.filter(User.display_name.like(f"%{params['display_name']}%"))
    if params.get("phone"):
        q = q.filter(User.phone == params["phone"])
    if params.get("role"):
        q = q.filter(User.role == params["role"])
    if params.get("status"):
        q = q.filter(User.status == params["status"])

    total = q.count()
    page = params.get("page", 1)
    page_size = params.get("page_size", 20)
    items = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return items, total


def get_user(db: Session, user_id: int) -> User:
    user = db.query(User).get(user_id)
    if not user:
        raise ValueError("用户不存在")
    return user


def update_user(db: Session, user_id: int, data: dict) -> User:
    """修改账号信息"""
    user = get_user(db, user_id)
    for field in ["display_name", "phone", "email", "department", "role"]:
        if field in data and data[field] is not None:
            setattr(user, field, data[field])
    user.updated_at = datetime.utcnow()
    db.commit()
    return user


def toggle_user_status(db: Session, user_id: int, admin_id: int):
    """冻结/解冻"""
    if user_id == admin_id:
        raise ValueError("不能操作自己的账号")
    user = get_user(db, user_id)
    user.status = "active" if user.status == "frozen" else "frozen"
    user.updated_at = datetime.utcnow()
    db.commit()
    return user


def reset_password(db: Session, user_id: int) -> str:
    """重置密码"""
    user = get_user(db, user_id)
    password = config.DEFAULT_INITIAL_PASSWORD

    db.add(PasswordHistory(user_id=user.id, password_hash=user.password_hash))
    user.password_hash = hash_password(password)
    user.is_first_login = 1
    user.password_updated_at = datetime.utcnow()
    user.locked_until = None
    user.failed_login_attempts = 0
    db.commit()

    return password
