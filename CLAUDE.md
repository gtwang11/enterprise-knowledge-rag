# CLAUDE.md — 运维数字员工门户

> Claude Code Agent 项目速查手册。接手任务先读这个，详细内容见 `docs/`。

## 项目概览

| 项 | 内容 |
|----|------|
| **名称** | 运维数字员工门户 (Enterprise Knowledge RAG) |
| **做什么** | 本地大模型 + RAG 知识库的运维智能问答系统，含工单流转闭环 |
| **架构** | Vue 3 前端 → FastAPI 后端 → SQLite + ChromaDB + Ollama |
| **Python** | 3.12，venv 在 `venv/` |
| **Node** | 18+，`frontend/` |

### 文档索引

| 文档 | 说明 |
|------|------|
| [系统概述](docs/系统概述.md) | 业务背景、角色、核心流程、约束 |
| [SRS](docs/SRS.md) | 软件需求规格说明书 |
| [SAD](docs/SAD.md) | 系统架构设计说明书 |
| [详细设计](docs/详细设计说明书.md) | 模块接口、算法、状态机 |
| [数据库设计](docs/数据库设计说明书.md) | ER 图、9 张表结构、索引 |
| [环境配置](docs/环境配置清单.md) | 硬件/软件安装/启动步骤 |
| [测试报告](docs/测试报告.md) | 81 用例、15 缺陷修复记录 |
| [用户手册](docs/用户手册.md) | 三角色操作指南 |
| [项目总结](docs/项目总结报告.md) | 踩坑记录、不足反思 |
| [可行性研究](docs/可行性研究报告.md) | 技经操可行性评估 |
| [开发计划](docs/项目开发计划.md) | WBS + 时间线 |

## Agent 工作环境

| 工具 | 环境 | 注意 |
|------|------|------|
| **Bash** | Git Bash | 正斜杠路径，POSIX 语法 |
| **PowerShell** | Windows PS 5.1 | 反斜杠路径，无 `&&`/`\|\|`，用 `; if ($?) {...}` |
| **Python** | `venv/Scripts/python.exe` | 3.12，依赖 `backend/requirements.txt` |

原则：文件操作用专用工具（Read/Write/Edit/Glob/Grep），不用 Bash/PS。

## 目录结构

```
backend/
├── main.py              # FastAPI 入口，注册路由，CORS
├── config.py            # 集中配置
├── database.py          # SQLAlchemy 引擎 + SessionLocal (WAL 模式)
├── dependencies.py      # 依赖注入（鉴权）
├── seed_data.py         # 种子数据：admin + 22 条 FAQ
├── engine/
│   ├── rag_pipeline.py       # RAG 管线编排
│   ├── vector_store.py       # ChromaDB 封装 + 原子热切换
│   ├── embedding_manager.py  # Ollama nomic-embed-text（768 维）
│   ├── llm_manager.py        # Ollama LLM 调用 + LLMError 异常
│   ├── text_preprocessor.py  # jieba 分词 + 正则清洗
│   └── prompts.py            # System Prompt + QA 模板
├── models/              # SQLAlchemy ORM（9 张表）
├── schemas/             # Pydantic 请求/响应 Schema
├── routers/             # FastAPI 路由（36 个端点）
├── services/            # 业务逻辑层
├── utils/               # 安全、日志、导入解析器
├── middleware/           # 限流中间件
├── data/                # SQLite DB + ChromaDB — gitignore
└── logs/                # 应用日志 — gitignore

frontend/
├── src/
│   ├── api/             # Axios API 封装
│   ├── views/           # Vue 页面组件（qa/tickets/faq/users/dashboard）
│   ├── router/          # Vue Router + beforeEach 鉴权守卫
│   ├── stores/          # Pinia 状态管理
│   └── layouts/         # 布局组件
└── vite.config.ts       # Vite 配置 + API 代理
```

## 关键配置

```python
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5:7b"
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIMENSION = 768
RAG_TOP_K = 5
RAG_SIMILARITY_THRESHOLD = 0.65
JWT_EXPIRE_MINUTES = 480
VECTORIZE_BATCH_SIZE = 10
VECTORIZE_BATCH_DELAY = 3
DEFAULT_INITIAL_PASSWORD = os.getenv("DEFAULT_INITIAL_PASSWORD", "123456")
```

## 核心流程

```
用户提问 → POST /api/qa/ask
  → RAGPipeline.execute(question)
    1. TextPreprocessor.process()    # jieba 分词 + 去停用词
    2. EmbeddingManager.embed()      # Ollama → 768 维向量
    3. VectorStore.search()          # ChromaDB 余弦 Top-K
    4. 判阈 (≥ 0.65)
    5. LLMManager.generate()         # Ollama 生成 / 降级引导工单
  → qa_history 写入 + 清理旧记录（保留 20 条）
```

向量重建采用原子热切换：写临时集合 → 指针切换 → 删旧集合，全程查询不中断。

## 常用命令

```bash
# 后端
cd backend && ../venv/Scripts/python.exe main.py    # uvicorn reload

# 前端
cd frontend && npm run dev

# 依赖
../venv/Scripts/pip.exe install -r backend/requirements.txt
cd frontend && npm install

# 测试
curl http://localhost:11434/api/tags                  # Ollama
python -c "import chromadb; c=chromadb.PersistentClient(path='backend/data/chromadb'); print(c.get_collection('faq_vectors').count())"  # ChromaDB
curl -s -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"123456"}'  # 登录
```

## Git

- `master` — 稳定主干
- `fix/*` — 修复分支，验证后合并回 master
- 改代码拉独立分支

## 外部依赖

| 服务 | 地址 | 用途 |
|------|------|------|
| Ollama | localhost:11434 | LLM + Embedding |
| ChromaDB | `backend/data/chromadb` | 向量存储 |
| SQLite | `backend/data/eknowledge.db` | 业务数据 |
