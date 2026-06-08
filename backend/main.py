"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库和种子数据"""
    init_db()
    from seed_data import seed_if_empty
    from database import SessionLocal
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="运维数字员工门户",
    description="基于 RAG 的运维智能问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from routers import auth, user, faq, qa, ticket, dashboard, health
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(faq.router)
app.include_router(qa.router)
app.include_router(ticket.router)
app.include_router(dashboard.router)
app.include_router(health.router)

# 生产模式：托管前端静态文件（如果存在）
static_dir = (Path(__file__).resolve().parent.parent / "frontend" / "dist").resolve()
index_file = static_dir / "index.html"

if static_dir.exists() and index_file.exists():
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        requested_path = (static_dir / full_path).resolve()
        if (
            full_path
            and requested_path.is_file()
            and (requested_path == static_dir or static_dir in requested_path.parents)
        ):
            return FileResponse(requested_path)

        return FileResponse(index_file)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
