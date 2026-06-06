"""仪表盘路由"""

import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_role
from models.user import User
from schemas.common import ApiResponse
from services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])


@router.get("/operator")
def operator_dashboard(user: User = Depends(require_role("operator")),
                       db: Session = Depends(get_db)):
    data = dashboard_service.get_operator_dashboard(db, user.id)
    return ApiResponse(code=200, message="success", data=data, timestamp=int(time.time() * 1000))


@router.get("/expert")
def expert_dashboard(user: User = Depends(require_role("expert")),
                     db: Session = Depends(get_db)):
    data = dashboard_service.get_expert_dashboard(db, user.id)
    return ApiResponse(code=200, message="success", data=data, timestamp=int(time.time() * 1000))


@router.get("/admin")
def admin_dashboard(user: User = Depends(require_role("admin")),
                    db: Session = Depends(get_db)):
    data = dashboard_service.get_admin_dashboard(db)
    return ApiResponse(code=200, message="success", data=data, timestamp=int(time.time() * 1000))
