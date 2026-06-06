"""FastAPI 依赖注入"""

import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config import (
    JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_REFRESH_THRESHOLD_MINUTES,
    DATA_DIR,
)
from database import get_db
from models.user import User
from models.token_blacklist import TokenBlacklist

security = HTTPBearer()

# JWT secret 文件路径
JWT_SECRET_FILE = os.path.join(DATA_DIR, ".jwt_secret")


def _get_jwt_secret() -> str:
    """获取或生成 JWT 密钥（文件持久化，不依赖 DB）"""
    if os.path.exists(JWT_SECRET_FILE):
        with open(JWT_SECRET_FILE, "r") as f:
            return f.read().strip()
    secret = uuid.uuid4().hex + uuid.uuid4().hex
    with open(JWT_SECRET_FILE, "w") as f:
        f.write(secret)
    return secret


def create_access_token(user_id: int, role: str) -> str:
    """签发 JWT"""
    secret = _get_jwt_secret()
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "role": role,
        "jti": uuid.uuid4().hex,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
        "iat": now,
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码 JWT，验证签名和过期时间"""
    secret = _get_jwt_secret()
    try:
        return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token无效")


def is_token_blacklisted(jti: str, db: Session) -> bool:
    """检查 Token 是否在黑名单"""
    return db.query(TokenBlacklist).filter(
        TokenBlacklist.token_jti == jti,
        TokenBlacklist.expired_at > datetime.utcnow()
    ).first() is not None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """获取当前登录用户（JWT 鉴权）"""
    token = credentials.credentials
    payload = decode_token(token)

    if is_token_blacklisted(payload["jti"], db):
        raise HTTPException(status_code=401, detail="Token已失效")

    user = db.query(User).get(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if user.status == "frozen":
        raise HTTPException(status_code=401, detail="账号已被冻结")

    # 检查锁定
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(status_code=401, detail="账号已被锁定")

    return user


def require_role(*roles: str):
    """角色鉴权依赖工厂"""
    async def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="无权限访问")
        return current_user
    return checker


def check_token_expiring(token: str) -> Optional[str]:
    """如果 Token 即将过期，返回新 Token"""
    try:
        secret = _get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        remaining = payload["exp"] - datetime.utcnow().timestamp()
        if remaining < JWT_REFRESH_THRESHOLD_MINUTES * 60:
            return create_access_token(int(payload["sub"]), payload["role"])
    except Exception:
        pass
    return None


def blacklist_token(token: str, db: Session):
    """将 Token 加入黑名单"""
    try:
        secret = _get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        db.add(TokenBlacklist(
            token_jti=payload["jti"],
            expired_at=datetime.fromtimestamp(payload["exp"]),
        ))
        db.commit()
    except Exception:
        pass
