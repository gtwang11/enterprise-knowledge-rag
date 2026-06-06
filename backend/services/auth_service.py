"""认证服务"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models.user import User
from models.password_history import PasswordHistory
from config import LOGIN_MAX_ATTEMPTS, LOGIN_LOCK_MINUTES
from dependencies import create_access_token, blacklist_token
from utils.security import hash_password, verify_password, validate_password_complexity


def authenticate(db: Session, username: str, password: str) -> dict:
    """登录认证，返回 Token 或抛出异常"""
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise ValueError("账号或密码错误")

    # 检查锁定
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
        raise ValueError(f"账号已被锁定，请在 {remaining} 分钟后重试")

    if user.status == "frozen":
        raise ValueError("账号已被冻结，请联系管理员")

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= LOGIN_MAX_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOGIN_LOCK_MINUTES)
            user.failed_login_attempts = 0
            db.commit()
            raise ValueError(f"密码错误次数过多，账号已锁定 {LOGIN_LOCK_MINUTES} 分钟")
        db.commit()
        raise ValueError("账号或密码错误")

    # 登录成功
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    db.commit()

    token = create_access_token(user.id, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 30 * 60,
        "role": user.role,
        "display_name": user.display_name,
        "is_first_login": bool(user.is_first_login),
    }


def change_password(db: Session, user: User, old_password: str, new_password: str, confirm_password: str):
    """修改密码"""
    if not verify_password(old_password, user.password_hash):
        raise ValueError("原密码错误")
    if new_password != confirm_password:
        raise ValueError("两次输入的密码不一致")

    ok, msg = validate_password_complexity(new_password)
    if not ok:
        raise ValueError(msg)

    # 检查密码历史
    recent_hashes = db.query(PasswordHistory).filter(
        PasswordHistory.user_id == user.id
    ).order_by(PasswordHistory.created_at.desc()).limit(3).all()

    for h in recent_hashes:
        if verify_password(new_password, h.password_hash):
            raise ValueError("新密码不能与前 3 次历史密码相同")

    # 保存历史
    db.add(PasswordHistory(user_id=user.id, password_hash=user.password_hash))

    # 更新密码
    user.password_hash = hash_password(new_password)
    user.is_first_login = 0
    user.password_updated_at = datetime.utcnow()
    db.commit()


def logout(db: Session, token: str):
    """登出：Token 加入黑名单"""
    blacklist_token(token, db)
