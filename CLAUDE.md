# CLAUDE.md — 运维数字员工门户

> 供 Claude Code Agent 使用的项目速查手册。新 Agent 接手任务时先读此文件。

## 项目概览

| 项目 | 说明 |
|------|------|
| **名称** | 运维数字员工门户 (Enterprise Knowledge RAG) |
| **架构** | FastAPI 后端 + Vue 3 前端 + ChromaDB 向量库 + Ollama LLM |
| **Python** | 3.12 (venv 在 `venv/`) |
| **Node** | `frontend/` 目录 |
| **背景** | 见 [PROJECT-BRIEF.md](./PROJECT-BRIEF.md) |
| **环境配置** | 见 [SETUP-CHECKLIST.md](./SETUP-CHECKLIST.md) |
| **需求文档** | [docs/SRS.md](./docs/SRS.md) |
| **架构文档** | [docs/SAD.md](./docs/SAD.md) |

## Agent 工作环境

| 工具 | 环境 | 注意 |
|------|------|------|
| **Bash** | Git Bash (Unix-like) | 正斜杠路径，POSIX 语法 |
| **PowerShell** | Windows PowerShell 5.1 | 反斜杠路径，无 `&&`/`||`，用 `; if ($?) {...}` |
| **Python** | `venv/Scripts/python.exe` | 3.12，依赖在 `backend/requirements.txt` |

**原则**：优先用专用工具（Read/Write/Edit/Glob/Grep），避免用 Bash/PowerShell 做文件操作。

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
│   ├── llm_manager.py        # Ollama qwen2.5:7b 调用 + LLMError 异常
│   ├── text_preprocessor.py  # jieba 分词 + 正则清洗
│   └── prompts.py            # System Prompt + QA 模板
├── models/              # SQLAlchemy ORM 模型
├── schemas/             # Pydantic 请求/响应 Schema
├── routers/             # FastAPI 路由层
├── services/            # 业务逻辑层
├── utils/               # 工具（安全、日志、导入解析器）
├── middleware/           # 中间件（频率限制，5分钟清理过期IP）
├── data/                # 运行时数据（SQLite DB + ChromaDB）— gitignore
└── logs/                # 应用日志 — gitignore

frontend/
├── src/
│   ├── api/             # Axios API 封装（qa.ts, faq.ts, auth.ts ...）
│   ├── views/           # Vue 页面组件
│   │   └── qa/QaView.vue    # 自助问答页面
│   ├── router/          # Vue Router + beforeEach 鉴权守卫
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
JWT_EXPIRE_MINUTES = 480
DEFAULT_INITIAL_PASSWORD = os.getenv("DEFAULT_INITIAL_PASSWORD", "123456")
VECTORIZE_BATCH_SIZE = 10
VECTORIZE_BATCH_DELAY = 3
```

## Q&A 自助问答流程（核心链路）

```
用户提问 → POST /api/qa/ask
  → qa_service.ask_question()
    → RAGPipeline.execute(question)
      1. TextPreprocessor.process()    # jieba 分词 + 去停用词，空结果→返回原文
      2. EmbeddingManager.embed()      # 调用 Ollama nomic-embed-text → 768维向量，失败抛异常
      3. VectorStore.search()          # ChromaDB 余弦相似度检索 Top-K
      4. 阈值判断 (>= 0.65)
      5. LLMManager.generate()         # 调用 Ollama qwen2.5:7b，失败抛 LLMError（含 fallback）
    → 写入 qa_history 表 + 清理旧记录(保留最近20条)
```

## 修复历史 (2026-06-06)

15 项问题全部修复，详见 `git log fix/chromadb-compat`：

| 优先级 | 要点 |
|--------|------|
| P0 | 硬编码密码→环境变量、Ticket.assigned_at 列、JWT expires_in→480min、ChromaDB 1.5.x 兼容、零向量检测 |
| P1 | 向量化 3 次重试、reindex ID 删除、LLMError 异常体系、限流定期清理、前端 beforeEach 守卫 |
| P2 | 批量导入分批+延迟、空文本预处理、CORS 具体 origins、移除未用参数、FAQ 分类统一降级 |

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
