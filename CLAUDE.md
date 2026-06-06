# CLAUDE.md — 运维数字员工门户

> 供 Claude Code Agent 使用的项目速查手册。新 Agent 接手任务时先读此文件。

## 项目概览

| 项目 | 说明 |
|------|------|
| **名称** | 运维数字员工门户 (Enterprise Knowledge RAG) |
| **架构** | FastAPI 后端 + Vue 3 前端 + ChromaDB 向量库 + Ollama LLM |
| **Python** | 3.12 (venv 在 `venv/`) |
| **Node** | `frontend/` 目录 |

## 目录结构

```
backend/
├── main.py              # FastAPI 入口，注册路由，CORS
├── config.py            # 集中配置（Ollama URL、模型名、阈值等）
├── database.py          # SQLAlchemy 引擎 + SessionLocal
├── dependencies.py      # FastAPI 依赖注入（鉴权等）
├── seed_data.py         # 首次启动种子数据：admin 账号 + 22 条 FAQ
├── engine/
│   ├── rag_pipeline.py       # RAG 主流程：预处理→Embedding→检索→判阈→LLM
│   ├── vector_store.py       # ChromaDB 封装（PersistentClient + 重试）
│   ├── embedding_manager.py  # Ollama nomic-embed-text 调用（768维）
│   ├── llm_manager.py        # Ollama qwen2.5:7b 调用
│   ├── text_preprocessor.py  # jieba 分词 + 正则清洗
│   └── prompts.py            # System Prompt + QA 模板
├── models/              # SQLAlchemy ORM 模型
├── schemas/             # Pydantic 请求/响应 Schema
├── routers/             # FastAPI 路由层
├── services/            # 业务逻辑层
├── utils/               # 工具（安全、日志、导入解析器）
├── middleware/           # 中间件（频率限制）
├── data/                # 运行时数据（SQLite DB + ChromaDB）— gitignore
└── logs/                # 应用日志 — gitignore

frontend/
├── src/
│   ├── api/             # Axios API 封装（qa.ts, faq.ts, auth.ts ...）
│   ├── views/           # Vue 页面组件
│   │   └── qa/QaView.vue    # 自助问答页面
│   ├── router/          # Vue Router + 权限守卫
│   ├── stores/          # Pinia 状态管理
│   └── layouts/         # 布局组件（Navbar, Sidebar）
└── vite.config.ts       # Vite 配置 + API 代理
```

## 关键配置 (`backend/config.py`)

```python
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5:7b"
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIMENSION = 768
RAG_TOP_K = 5
RAG_SIMILARITY_THRESHOLD = 0.65
CHROMA_COLLECTION_NAME = "faq_vectors"
LLM_TIMEOUT_SECONDS = 30
```

## Q&A 自助问答流程（核心链路）

```
用户提问 → POST /api/qa/ask
  → qa_service.ask_question()
    → RAGPipeline.execute(question)
      1. TextPreprocessor.process()    # jieba 分词 + 去停用词
      2. EmbeddingManager.embed()      # 调用 Ollama nomic-embed-text → 768维向量
      3. VectorStore.search()          # ChromaDB 余弦相似度检索 Top-K
      4. 阈值判断 (>= 0.65)
      5. LLMManager.generate()         # 调用 Ollama qwen2.5:7b 生成回答
    → 写入 qa_history 表 + 清理旧记录(保留最近20条)
```

## 代码审查报告

完整审查报告见 **[PROJECT_REVIEW.md](./PROJECT_REVIEW.md)**，包含 22 项问题和修复建议。

## 当前已知问题 (2026-06-06)

### P0 — 严重 → ✅ 全部修复

1. ✅ **硬编码初始密码 "123456"**: 改用 `config.DEFAULT_INITIAL_PASSWORD` + 环境变量 `DEFAULT_INITIAL_PASSWORD`
2. ✅ **`claim_ticket` 设置不存在的字段**: Ticket 模型新增 `assigned_at` 列
3. ✅ **JWT expires_in 与实际不一致**: 2 处 `30*60` 改为 `JWT_EXPIRE_MINUTES * 60`
4. ✅ **ChromaDB 版本不兼容**: 线程锁保护客户端创建，版本约束 `>=0.5.0,<2.0.0`
5. ✅ **Embedding 零向量未检测**: 失败时抛出异常，rag_pipeline 优雅降级

### P1 — 中等 → ✅ 全部修复

6. ✅ **向量库不完整**: 后台向量化加重试（3次指数退避），批次间延迟 + 命名的非daemon线程日志
7. ✅ **`reindex_all_faqs` 无回滚**: ChromaDB 1.5.x 改用 ID 逐个删除，避免 where={} 不兼容
8. ✅ **LLM 异常被吞没**: 自定义 `LLMError` 异常，按错误类型区分（Timeout/Connection/HTTPError），rag_pipeline 显式捕获
9. ✅ **限流中间件内存泄漏**: 空列表删除 key，每 5 分钟全量清理过期 IP
10. ✅ **前端路由无鉴权守卫**: `beforeEach` 检查 token + role，未登录跳 /login，越权跳 /403

### P2 — 技术债务 → ✅ 全部修复

11. ✅ **Ollama Embedding 超时**: faq_service 批量导入分批处理（每10条休息3秒）
12. ✅ **文本预处理空结果**: 全特殊字符输入提前检测，警告日志 + 返回原始文本
13. ✅ **CORS 不安全组合**: `allow_origins` 改为具体 origin 列表（localhost:5173/8000）
14. ✅ **未使用的 `admin_id` 参数**: 从 `create_user` 签名中移除
15. ✅ **FAQ 导入器分类不一致**: 空分类和错误分类统一降级为"其他"+ warning（不再 reject）

## 常用命令

```bash
# 后端启动
cd backend
../venv/Scripts/python.exe main.py          # 开发模式 (uvicorn reload)

# 前端启动
cd frontend
npm run dev

# 安装依赖
../venv/Scripts/pip.exe install -r backend/requirements.txt
cd frontend && npm install

# 查看日志
cat backend/logs/app.log

# 测试 Ollama
curl http://localhost:11434/api/tags

# 测试 ChromaDB
python -c "import chromadb; c=chromadb.PersistentClient(path='backend/data/chromadb'); print(c.get_collection('faq_vectors').count())"
```

## Git 分支策略

- `master` - 稳定主干
- `fix/*` - 修复分支，验证通过后合并回 master
- 每次修改拉独立分支，不改 master 直接

## 外部依赖

| 服务 | 地址 | 用途 |
|------|------|------|
| Ollama | localhost:11434 | LLM 推理 + Embedding |
| ChromaDB | 本地文件 `backend/data/chromadb` | 向量存储与检索 |
| SQLite | 本地文件 `backend/data/eknowledge.db` | 业务数据 |
