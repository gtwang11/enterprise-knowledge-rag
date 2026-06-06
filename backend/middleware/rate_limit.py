"""IP 限流中间件"""

import time
from collections import defaultdict

from fastapi import Request, HTTPException

# 内存限流计数器
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_last_cleanup_at: float = time.time()


def _periodic_cleanup(window_seconds: int):
    """定期清理不活跃 IP 的过期记录，防止内存泄漏"""
    global _last_cleanup_at
    now = time.time()
    # 每 5 分钟清理一次，避免每次请求都全量扫描
    if now - _last_cleanup_at < 300:
        return
    _last_cleanup_at = now
    stale_ips = [
        ip for ip, times in _rate_limit_store.items()
        if not times or all(now - t >= window_seconds for t in times)
    ]
    for ip in stale_ips:
        del _rate_limit_store[ip]


def rate_limit_middleware(max_requests: int = 10, window_seconds: int = 60):
    """登录接口限流：同一 IP 每分钟最多 max_requests 次"""
    async def middleware(request: Request, call_next):
        if request.url.path == "/api/auth/login" and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            # 清理过期记录
            times = [t for t in _rate_limit_store[client_ip] if now - t < window_seconds]
            if times:
                _rate_limit_store[client_ip] = times
            else:
                _rate_limit_store.pop(client_ip, None)  # 无有效记录则删除 key

            if len(_rate_limit_store.get(client_ip, [])) >= max_requests:
                raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
            _rate_limit_store[client_ip].append(now)

        _periodic_cleanup(window_seconds)
        response = await call_next(request)
        return response
    return middleware
