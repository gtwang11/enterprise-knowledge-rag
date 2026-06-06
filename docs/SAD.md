# 系统架构设计说明书 (SAD)

## 运维数字员工门户系统

| 文档版本 | 日期 | 修改说明 | 作者 |
|---------|------|---------|------|
| V1.0 | 2026-06-06 | 初稿 | 架构组 |

---

## 1. 架构总览

系统采用经典的四层 Web 架构：前端展示层 → 后端 API 层 → 数据持久层，AI 能力作为独立的引擎层由后端调用。

```
===============================================================================
                    运维数字员工门户系统 -- 总体架构图
===============================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                      前端展示层 (Vue 3 + Element Plus)                       │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ 问答页面  │  │ 工单页面  │  │ FAQ管理   │  │ 账号管理  │  │ 仪表盘   │     │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘     │
│        └─────────────┴─────────────┴─────────────┴─────────────┘           │
│                                  │                                         │
│                     Axios HTTP 客户端 (Token 自动注入/刷新)                   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ REST API (JSON) / JWT 鉴权
                                   │ 开发: 5173→proxy→8000 / 生产: 8000
┌──────────────────────────────────┴──────────────────────────────────────────┐
│                      后端 API 层 (FastAPI + Python 3.10+)                    │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ auth     │  │ user     │  │ faq      │  │ qa       │  │ ticket   │     │
│  │ 模块     │  │ 模块     │  │ 模块     │  │ 模块     │  │ 模块     │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                                             │
│  中间件层: JWT 鉴权 / 角色鉴权(Dependency Injection) / 限流 / 日志           │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │          RAG 引擎层 (LangChain + ChromaDB + Ollama)                  │  │
│  │  预处理(jieba)→ Embedding(Ollama)→ ChromaDB检索(K=5)→ 判阈(0.65)→  │  │
│  │  LLM生成(DeepSeek) / 降级引导工单                                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ SQLite / ChromaDB 文件 I/O
┌──────────────────────────────────┴──────────────────────────────────────────┐
│                      数据持久层                                              │
│  ┌────────────────────┐  ┌────────────────────┐                            │
│  │ SQLite             │  │ ChromaDB           │                            │
│  │ data/eknowledge.db │  │ data/chromadb/     │                            │
│  │ 9 张业务表          │  │ 768 维向量存储      │                            │
│  └────────────────────┘  └────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │ HTTP API
┌──────────────────────────────────┴──────────────────────────────────────────┐
│                 AI 推理层 (独立进程 Ollama, localhost:11434)                 │
│  ┌────────────────────────┐  ┌────────────────────────┐                    │
│  │ deepseek-llm-7b-chat:q4│  │ nomic-embed-text       │                    │
│  │ 内存 ~4.5GB            │  │ 内存 ~0.3GB, 768维     │                    │
│  └────────────────────────┘  └────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 技术栈确定说明

| 层次 | 技术 | 版本 | 选择理由 |
|------|------|------|----------|
| 后端框架 | FastAPI | ≥0.110 | Python 异步框架，原生 async/await，自动生成 OpenAPI 文档，与 LangChain/Ollama 生态无缝集成 |
| 前端框架 | Vue 3 | ≥3.4 | Composition API 逻辑复用，TypeScript 友好，体积小，企业级后台事实标准 |
| UI 组件库 | Element Plus | ≥2.6 | 成熟中文 UI 组件库，表格/表单/对话框等企业场景全覆盖 |
| 构建工具 | Vite | ≥5.0 | 秒级热更新，构建速度快，原生支持 Vue SFC |
| 关系数据库 | SQLite | 3.x | Python 内置，零配置零进程，单机 10 万条内性能完全胜任 |
| 向量数据库 | ChromaDB | ≥0.5 | 轻量 Python 原生，嵌入式运行，与 LangChain 原生集成 |
| ORM | SQLAlchemy | ≥2.0 | FastAPI 官方推荐异步 ORM，类型安全 |
| LLM 推理 | Ollama | ≥0.1.32 | 一键加载模型，REST API，自动管理 CPU/GPU 推理 |
| LLM 模型 | deepseek-llm-7b-chat:q4 | 4-bit | 7B 参数，量化后 ~4.5GB，中文能力优秀，单次生成 3-8 秒 |
| Embedding | nomic-embed-text | latest | 274MB，768 维，内存 ~0.3GB，支持中文 |
| RAG 框架 | LangChain | ≥0.2 | 标准化 RAG 管线，ChromaDB/Ollama 封装开箱即用 |
| JWT | PyJWT | ≥2.8 | HS256 对称签名，单机无需 RSA 密钥对管理 |
| 密码哈希 | bcrypt | ≥4.1 | 业界标准，cost=12 |
| 前端 HTTP | Axios | ≥1.6 | 请求/响应拦截器，Token 自动注入和刷新 |
| 前端路由 | Vue Router | ≥4.2 | 导航守卫，角色权限控制 |
| 状态管理 | Pinia | ≥2.1 | Vue 3 官方状态管理，TypeScript 类型推导完善 |

---

## 3. 后端模块设计

### 3.1 目录结构

```
backend/
├── main.py                    # FastAPI 入口，注册路由和中间件
├── config.py                  # 集中配置（DB路径、Ollama URL、JWT密钥等）
├── database.py                # SQLAlchemy 引擎和会话工厂
├── dependencies.py            # 依赖注入（获取当前用户、DB Session）
├── models/                    # SQLAlchemy ORM 模型
│   ├── user.py / password_history.py / token_blacklist.py
│   ├── faq.py / ticket.py / ticket_log.py
│   ├── qa_history.py / operation_log.py / system_config.py
├── schemas/                   # Pydantic 请求/响应模型
│   ├── auth.py / user.py / faq.py / qa.py / ticket.py / common.py
├── routers/                   # API 路由（按模块拆分）
│   ├── auth.py / user.py / faq.py / qa.py
│   ├── ticket.py / dashboard.py / health.py
├── services/                  # 业务逻辑层
│   ├── auth_service.py        # 登录/登出/Token签发与验证/密码修改
│   ├── user_service.py        # 账号CRUD/密码重置/冻结解冻
│   ├── faq_service.py         # FAQ CRUD/批量导入导出/向量库同步
│   ├── qa_service.py          # 问答编排：调用RAG管线+记录历史
│   ├── ticket_service.py      # 工单状态机驱动
│   ├── dashboard_service.py   # 各角色仪表盘统计
│   └── operation_log_service.py
├── engine/                    # RAG 引擎层
│   ├── rag_pipeline.py        # RAG管线编排（核心类）
│   ├── text_preprocessor.py   # jieba分词/去停用词/特殊字符过滤
│   ├── embedding_manager.py   # Ollama nomic-embed-text 接口封装
│   ├── vector_store.py        # ChromaDB封装：增删改查+重试机制
│   ├── llm_manager.py         # Ollama DeepSeek 接口封装
│   └── prompts.py             # System Prompt + QA Prompt 模板
├── middleware/                 # FastAPI 中间件
│   ├── auth_middleware.py     # JWT 鉴权
│   ├── role_middleware.py     # 角色鉴权 (Dependency Injection)
│   └── rate_limit.py          # 登录限流
├── utils/
│   ├── security.py            # bcrypt哈希/随机密码/复杂度校验
│   ├── ticket_no_generator.py # 工单编号生成
│   ├── faq_importer.py        # Excel/CSV 解析
│   └── logger.py              # 日志配置
├── seed_data.py               # 初始化：20+条FAQ + admin账号
├── requirements.txt
└── data/                      # 运行时生成
    ├── eknowledge.db
    └── chromadb/
```

### 3.2 核心模块职责

**config.py** — 集中管理所有配置常量：
```
DB_PATH, CHROMA_DB_PATH, OLLAMA_BASE_URL="http://localhost:11434"
LLM_MODEL="deepseek-llm-7b-chat:q4", EMBEDDING_MODEL="nomic-embed-text"
JWT_ALGORITHM="HS256", JWT_EXPIRE_MINUTES=30
PASSWORD_BCRYPT_COST=12, LOGIN_MAX_ATTEMPTS=5, LOGIN_LOCK_MINUTES=15
RAG_TOP_K=5, RAG_SIMILARITY_THRESHOLD=0.65, RAG_MAX_RETRIES=3
```

**services/ticket_service.py** — 工单状态机，严格约束状态转移矩阵，校验操作者身份，所有变更记录 ticket_logs。

**services/faq_service.py** — FAQ CRUD，每次变更后调用 vector_store 同步向量库，失败触发重试（3次/5秒）。

**engine/vector_store.py** — ChromaDB 封装：`add_faq()` `delete_faq()` `update_faq()` `search()`，每方法有重试机制。

---

## 4. 前端模块设计

### 4.1 目录结构

```
frontend/
├── vite.config.ts              # Vite 配置（代理 /api → localhost:8000）
├── src/
│   ├── main.ts                 # Vue 入口：注册 Router/Pinia/ElementPlus
│   ├── App.vue                 # 根组件
│   ├── router/
│   │   ├── index.ts            # 路由定义
│   │   └── permission.ts       # 导航守卫：Token检查+角色路由过滤
│   ├── stores/
│   │   ├── user.ts             # 用户信息/Token/角色
│   │   └── app.ts              # 全局状态
│   ├── api/
│   │   ├── request.ts          # Axios实例：Token注入/401处理/自动刷新
│   │   ├── auth.ts / user.ts / faq.ts / qa.ts / ticket.ts / dashboard.ts
│   ├── layouts/
│   │   ├── MainLayout.vue      # 侧边栏+顶栏+内容区
│   │   ├── Sidebar.vue         # 角色动态菜单
│   │   └── EmptyLayout.vue     # 登录页布局
│   ├── views/
│   │   ├── login/LoginView.vue
│   │   ├── qa/QaView.vue                    # operator 问答主页
│   │   ├── tickets/MyTicketsView.vue        # operator 我的工单
│   │   ├── tickets/PendingTicketsView.vue   # expert 待处理队列
│   │   ├── tickets/TicketDetailView.vue     # 工单详情（按角色展示不同操作按钮）
│   │   ├── faq/FaqListView.vue              # FAQ 列表+查询
│   │   ├── faq/FaqFormView.vue              # FAQ 新增/编辑
│   │   ├── faq/FaqImportView.vue            # 批量导入
│   │   ├── users/UserListView.vue           # 账号管理
│   │   ├── users/UserFormView.vue           # 账号创建/编辑
│   │   ├── dashboard/DashboardView.vue      # 角色仪表盘
│   │   ├── profile/ProfileView.vue          # 个人信息+修改密码
│   │   └── error/NotFoundView.vue + ForbiddenView.vue
│   ├── components/
│   │   ├── common/              # Pagination/StatusTag/UrgencyTag/ConfirmDialog
│   │   ├── qa/                  # ChatMessage/QuestionInput/ChatHistory
│   │   ├── tickets/             # TicketTable/SolutionEditor/Timeline
│   │   ├── faq/                 # FaqTable/FaqCategorySelect/FaqImportResult
│   │   └── dashboard/           # StatCard/TrendChart(ECharts)
│   └── styles/                  # global.scss/variables.scss
```

### 4.2 路由守卫逻辑

每次导航前：① 检查是否已登录（无 Token 且目标非 /login → 跳转登录）；② 已登录访问 /login → 根据角色跳转首页；③ 目标路由 meta.roles 不含当前角色 → 跳 /403；④ Axios 拦截 401 → 清除 Token 跳转登录。

---

## 5. RAG 引擎详细设计

### 5.1 管线流程

```
用户问题 Q
  → TextPreprocessor (jieba分词/去停用词/特殊字符过滤)
  → EmbeddingManager (POST Ollama /api/embed, nomic-embed-text → 768维)
  → VectorStore.search (ChromaDB 余弦相似度, K=5, 过滤 status='published')
  → 判阈: max_similarity ≥ 0.65?
       ├── 是 → LLMManager.generate (DeepSeek 7B, Temp=0.1, MaxToken=1024)
       │        → 返回回答 + FAQ来源引用
       └── 否 → 返回降级: "无法找到相关答案，是否创建工单？"
  → 记录 qa_history (question/answer/similarity/processing_time_ms)
```

### 5.2 Prompt 模板

**系统指令**:
```
你是一个企业内部运维支持AI助手。基于提供的知识库内容准确回答运维技术问题。
规则：① 只基于知识库内容回答，不足时说明"知识库中未找到相关信息"
② 回答简洁准确，使用中文 ③ 含步骤时分步列出
④ 不添加知识库外信息 ⑤ 与运维无关礼貌说明超出范围 ⑥ 末尾列出参考FAQ ID
```

**问答模板**: `{system_instruction}\n\n参考知识库内容：\n{context}\n\n用户问题：{question}\n\nAI回答：`

### 5.3 参数配置

| 参数 | 值 | 说明 |
|------|-----|------|
| RAG_TOP_K | 5 | 检索返回的最相似 FAQ 数 |
| RAG_SIMILARITY_THRESHOLD | 0.65 | 余弦相似度阈值 |
| RAG_MAX_RETRIES | 3 | 向量库操作失败重试次数 |
| RAG_RETRY_INTERVAL | 5s | 重试间隔 |
| LLM_TEMPERATURE | 0.1 | 低温度确保回答确定性 |
| LLM_MAX_TOKENS | 1024 | 单次生成上限 |
| LLM_TIMEOUT | 30s | 调用超时 |
| EMBEDDING_DIMENSION | 768 | nomic-embed-text 输出维度 |

---

## 6. 数据流设计

### 6.1 问答数据流

```
operator → 输入问题 → POST /api/qa/ask → RAG Pipeline:
  预处理 → Embedding(Ollama) → ChromaDB检索 → 判阈(0.65)
    → 通过: LLM生成(DeepSeek) → 返回回答+来源
    → 不通过: 返回降级提示+"创建工单"按钮
  → 记录 qa_history(SQLite) → 前端展示结果
```

### 6.2 工单流转数据流

```
operator创建工单 → [待处理]
expert领取 → [处理中] (写入 handler_id, 记录 ticket_logs)
expert提交方案 → [待回访确认]
operator确认解决 → [已完成] → expert一键录入 → FAQ表+向量库
operator反馈未解决 → [处理中] (回退)
expert退回 → [待处理] (清空 handler_id, 必填退回原因)
```

### 6.3 FAQ 管理 + 向量同步流

```
FAQ新增 → SQLite INSERT → vector_store.add() ─┬→ 成功 √
                                                └→ 失败 → 重试(5s)→重试(5s)→重试(5s)→ERROR日志
FAQ修改 → SQLite UPDATE → vector_store.delete() + add() (同上重试)
FAQ删除 → SQLite DELETE → vector_store.delete() (同上重试)
```

---

## 7. 部署架构

### 7.1 进程拓扑

```
单机 4C8G:
  进程1: Ollama Server (127.0.0.1:11434)
    - deepseek-llm-7b-chat:q4  常驻 ~4.5GB
    - nomic-embed-text         常驻 ~0.3GB
  进程2: Python FastAPI (0.0.0.0:8000)
    - uvicorn 单进程 + 异步任务(RAG管线/LLM调用)
  进程3: Vite Dev Server (开发) / FastAPI静态托管 (生产)
    - 开发: :5173 代理 /api → :8000
    - 生产: npm build → dist/ 由 FastAPI 托管，单端口 8000
```

### 7.2 内存预算

| 组件 | 内存 |
|------|------|
| Ollama + DeepSeek-7B (4-bit) | ~4.5 GB |
| Ollama + nomic-embed-text | ~0.3 GB |
| Python FastAPI 后端 | ~0.3 GB |
| Vite Dev Server (开发) | ~0.3 GB |
| ChromaDB (10000条FAQ) | ~0.1 GB |
| SQLite | ~0.05 GB |
| OS (Windows/Linux) | ~1.5 GB |
| 安全余量 | ~0.85 GB |
| **总计** | **~7.9 GB (≤ 8GB)** |

生产模式下前端静态托管可省去 Vite ~0.3GB，余量更大。Linux 无 GUI 可再省 ~0.7GB。

### 7.3 启动顺序

```
步骤1: ollama serve (等待 :11434 就绪, ~5s)
步骤2: 检查模型 → 不存在则 ollama pull (首次联网)
步骤3: cd backend && python main.py
  → 检查/创建 SQLite → 建表
  → faq表为空则 seed_data.py (预置20+FAQ+向量化+admin账号)
  → uvicorn :8000
步骤4: cd frontend && npm run dev (开发) 或 npm run build (生产)
```

### 7.4 端口分配

| 服务 | 端口 | 绑定 | 说明 |
|------|------|------|------|
| Ollama | 11434 | 127.0.0.1 | 仅本地 |
| FastAPI | 8000 | 0.0.0.0 | API + Swagger /docs |
| Vite | 5173 | 0.0.0.0 | 仅开发 |

---

## 8. 安全设计

### 8.1 JWT 鉴权流程

```
登录: POST /api/auth/login {username, password}
  → bcrypt验证密码 → 检查账号状态/锁定
  → 签发JWT: {sub:user_id, role:"operator", jti:uuid, exp:now+30min}
  → 前端存储到 localStorage + Pinia

后续请求: Authorization: Bearer <token>
  → auth_middleware: 解码JWT → 检查jti黑名单 → 检查exp → 注入current_user
  → role_middleware: 检查路由角色权限 (通过 Depends(require_role(...)))
  → Token剩余<5min: 响应Header返回新Token

登出: POST /api/auth/logout
  → jti写入token_blacklist表 → 该Token永久失效
```

### 8.2 角色鉴权（依赖注入方式，非全局中间件）

```python
def require_role(*roles: str):
    async def checker(current_user = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(403, "无权限访问")
        return current_user
    return checker

# 路由示例
@router.get("/api/faq")
async def list_faqs(current_user = Depends(require_role("admin", "expert"))): ...
@router.post("/api/faq")
async def create_faq(current_user = Depends(require_role("admin"))): ...
```

选择依赖注入而非全局中间件的理由：32 个 API 端点权限组合多样，依赖注入将权限与路由绑定在同一处，修改路由不会遗漏同步权限。

### 8.3 密码策略

| 项 | 规则 | 实现 |
|----|------|------|
| 最小长度 | 8 位 | 前后端双重校验 |
| 复杂度 | 大小写字母+数字+特殊字符至少3类 | utils/security.py |
| 加密 | bcrypt, cost=12 | utils/security.py |
| 历史 | 不重复前3次 | 查询 password_history 表 |
| 首次登录 | is_first_login=1，强制提示改密码 | auth_service.py |

### 8.4 登录限流

- 同一 IP 每分钟 ≤ 10 次请求 (内存计数器，429 Too Many Requests)
- 同一账号连续 5 次错误 → 锁定 15 分钟 (持久化 users 表)

### 8.5 Token 黑名单

登出时 jti 写入 token_blacklist 表，鉴权时连带查询 `expired_at > now()` 过滤已过期记录，避免表无限增长。

---

## 9. 关键设计决策记录

### D-1: 鉴权用依赖注入而非全局中间件
路由和权限绑定在同一处（Depends 声明），修改路由时不会遗漏同步权限。全局中间件需要维护 URL 模式匹配表，维护成本高且易遗漏。

### D-2: RAG 引擎作为后端进程内模块而非独立服务
单机 4C8G 不允许额外服务进程。LLM/Embedding 已通过 Ollama 分离，RAG 管线编排是纯 CPU+I/O，与 FastAPI 同进程无瓶颈。拆分微服务会增加 ~200MB 内存压力。

### D-3: JWT 用 HS256 而非 RS256
单机部署无多服务独立验证 JWT 的场景。HS256 对称签名实现简单，密钥首次启动随机生成并持久化到 system_config 表。RS256 需管理 RSA 密钥对，安全收益在单机场景下为零。

### D-4: SQLite 而非 PostgreSQL/MySQL
零配置零进程，符合"直接启动"约束（C-02）。9 张表数据量不超 10 万条，SQLite 完全胜任。引入 PostgreSQL 需额外安装配置数据库服务，违反约束。

### D-5: 通过 Ollama API 而非 Python 直接加载模型
Ollama 自动管理模型生命周期和 CPU 推理。若在 Python 进程中直接用 transformers/llama.cpp 加载 7B 模型，进程内存从 300MB 飙升到 5GB+，导致后端不稳定。HTTP 调用隔离进程，崩溃互不影响。

### D-6: Token 存 localStorage 而非 httpOnly Cookie
SPA 需通过 JS 读取 Token 设置请求头。localStorage 实现简单，刷新不丢失。httpOnly Cookie 安全性更高但前端无法感知过期时间，无法实现"会话过期前 1 分钟弹窗续期"（F-1.3 第 4 条）。本系统内网单机部署，XSS 攻击面极小。

### D-7: Embedding 和 LLM 共用同一 Ollama 实例
Ollama 原生支持同时加载多个模型，自动管理内存。两个模型通过不同 API 路径（/api/embed 和 /api/chat）区分。启动两个实例会浪费 ~50MB 进程基础内存。

### D-8: 重试 3 次间隔 5 秒
ChromaDB 文件型数据库写入失败通常是瞬时文件锁争用或磁盘 I/O 延迟。5 秒间隔让锁释放，3 次重试在 15 秒内完成（不超 FAQ 新增 F-3.1 的响应时限）。超过 3 次属持久性故障，记录 ERROR 日志由人工介入。

### D-9: 前端开发期使用 Vite 代理而非 CORS
代理对浏览器透明，无跨域问题，无 OPTIONS 预检开销。生产模式前端静态文件由 FastAPI 托管（同源），根本不存在跨域。使用 CORS 需要后端为 32 个端点额外处理预检请求。

---

*文档结束。本架构设计说明书与 SRS V1.1 完全对齐，所有技术决策均已确定，作为后续详细设计和编码实现的架构基线。*
