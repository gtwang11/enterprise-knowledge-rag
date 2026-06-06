"""IP 限流中间件"""

import time
from collections import defaultdict

from fastapi import Request, HTTPException

# 内存限流计数器
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


def rate_limit_middleware(max_requests: int = 10, window_seconds: int = 60):
    """登录接口限流：同一 IP 每分钟最多 max_requests 次"""
    async def middleware(request: Request, call_next):
        if request.url.path == "/api/auth/login" and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            # 清理过期记录
            _rate_limit_store[client_ip] = [
                t for t in _rate_limit_store[client_ip]
                if now - t < window_seconds
            ]
            if len(_rate_limit_store[client_ip]) >= max_requests:
                raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
            _rate_limit_store[client_ip].append(now)

        response = await call_next(request)
        return response
    return middleware
