"""健康检查路由"""

import time
from fastapi import APIRouter

from schemas.common import ApiResponse

router = APIRouter(prefix="/api", tags=["系统"])


@router.get("/health")
def health_check():
    return ApiResponse(code=200, message="OK", data={"status": "running"},
                       timestamp=int(time.time() * 1000))
