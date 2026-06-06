"""账号管理路由"""

import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_role
from models.user import User
from schemas.user import UserCreate, UserUpdate, UserQuery, UserOut
from schemas.common import ApiResponse, PageData
from services import user_service

router = APIRouter(prefix="/api/users", tags=["账号管理"])


@router.get("")
def list_users(
    username: str = None, display_name: str = None, phone: str = None,
    role: str = None, status: str = None, page: int = 1, page_size: int = 20,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    params = {"username": username, "display_name": display_name, "phone": phone,
              "role": role, "status": status, "page": page, "page_size": page_size}
    items, total = user_service.query_users(db, params)

    out_items = []
    for u in items:
        out_items.append(UserOut(
            id=u.id, username=u.username, display_name=u.display_name,
            phone=u.phone, email=u.email, department=u.department,
            role=u.role, status=u.status,
            is_first_login=bool(u.is_first_login),
            last_login_at=u.last_login_at.strftime("%Y-%m-%d %H:%M:%S") if u.last_login_at else None,
            created_at=u.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ))

    total_pages = (total + page_size - 1) // page_size
    return ApiResponse(code=200, message="success", data=PageData(
        items=out_items, total=total, page=page, page_size=page_size, total_pages=total_pages
    ).model_dump(), timestamp=int(time.time() * 1000))


@router.post("")
def create_user(req: UserCreate, db: Session = Depends(get_db),
                admin: User = Depends(require_role("admin"))):
    try:
        user = user_service.create_user(db, req.model_dump())
        from services.operation_log_service import log_operation
        log_operation(db, admin.id, "create_user", "user", user.id, f"创建账号 {user.username}")
        return ApiResponse(code=201, message="success", data={
            "id": user.id, "username": user.username,
            "initial_password": getattr(user, "_initial_password", ""),
        }, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db),
             admin: User = Depends(require_role("admin"))):
    try:
        user = user_service.get_user(db, user_id)
        return ApiResponse(code=200, message="success", data=UserOut(
            id=user.id, username=user.username, display_name=user.display_name,
            phone=user.phone, email=user.email, department=user.department,
            role=user.role, status=user.status,
            is_first_login=bool(user.is_first_login),
            last_login_at=user.last_login_at.strftime("%Y-%m-%d %H:%M:%S") if user.last_login_at else None,
            created_at=user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ).model_dump(), timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=404, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.put("/{user_id}")
def update_user(user_id: int, req: UserUpdate, db: Session = Depends(get_db),
                admin: User = Depends(require_role("admin"))):
    try:
        user_service.update_user(db, user_id, req.model_dump(exclude_none=True))
        from services.operation_log_service import log_operation
        log_operation(db, admin.id, "update_user", "user", user_id)
        return ApiResponse(code=200, message="账号信息已更新", data=None, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.patch("/{user_id}/status")
def toggle_status(user_id: int, db: Session = Depends(get_db),
                  admin: User = Depends(require_role("admin"))):
    try:
        user = user_service.toggle_user_status(db, user_id, admin.id)
        from services.operation_log_service import log_operation
        log_operation(db, admin.id, "toggle_user_status", "user", user_id,
                      f"状态变更为 {user.status}")
        return ApiResponse(code=200, message=f"账号已{'解冻' if user.status == 'active' else '冻结'}",
                           data=None, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db),
                admin: User = Depends(require_role("admin"))):
    try:
        target = user_service.get_user(db, user_id)
        if target.username == "admin":
            return ApiResponse(code=400, message="不能删除admin账号", data=None, timestamp=int(time.time() * 1000))
        db.delete(target)
        db.commit()
        from services.operation_log_service import log_operation
        log_operation(db, admin.id, "delete_user", "user", user_id, f"删除账号 {target.username}")
        return ApiResponse(code=200, message="账号已删除", data=None, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, db: Session = Depends(get_db),
                   admin: User = Depends(require_role("admin"))):
    try:
        password = user_service.reset_password(db, user_id)
        from services.operation_log_service import log_operation
        log_operation(db, admin.id, "reset_password", "user", user_id)
        return ApiResponse(code=200, message="success", data={
            "new_password": password,
            "tip": "请记录此密码并告知用户",
        }, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))
