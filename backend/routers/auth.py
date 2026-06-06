"""认证路由"""

import time
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, check_token_expiring
from models.user import User
from schemas.auth import LoginRequest, ChangePasswordRequest
from schemas.common import ApiResponse
from services import auth_service
from config import JWT_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = auth_service.authenticate(db, req.username, req.password)
        return ApiResponse(code=200, message="success", data=result, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    auth_service.logout(db, token)
    return ApiResponse(code=200, message="success", data=None, timestamp=int(time.time() * 1000))


@router.put("/change-password")
def change_password(req: ChangePasswordRequest,
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    try:
        auth_service.change_password(db, user, req.old_password, req.new_password, req.confirm_password)
        return ApiResponse(code=200, message="密码已修改，请重新登录", data=None, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.post("/refresh")
def refresh_token(request: Request, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    new_token = check_token_expiring(token)
    if new_token:
        return ApiResponse(code=200, message="success", data={
            "access_token": new_token, "token_type": "bearer", "expires_in": JWT_EXPIRE_MINUTES * 60
        }, timestamp=int(time.time() * 1000))
    return ApiResponse(code=200, message="Token未过期", data=None, timestamp=int(time.time() * 1000))
