# 运维数字员工门户

课题六“运维数字员工的建设”的核心实现：本地大模型与 RAG 私有知识库结合，为一线运维提供自助问答，并通过工单处理和知识回灌形成闭环。

## 核心流程

```text
一线运维提问
  -> nomic-embed-text 生成问题向量
  -> ChromaDB Top-K 检索（异常时使用 SQLite 向量兜底）
  -> 相似度达到阈值后，将 FAQ 上下文交给 qwen2.5:7b 生成回答
  -> 无法解决时创建工单
  -> 资深专家领取并提交方案
  -> 一线运维确认解决
  -> 专家或管理员将方案录入 FAQ
```

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router、Axios
- 后端：FastAPI、SQLAlchemy、Pydantic、JWT
- 业务数据：SQLite
- 向量检索：ChromaDB + SQLite 兜底向量表
- 本地推理：Ollama `qwen2.5:7b`
- 向量模型：Ollama `nomic-embed-text`（768 维）

项目采用自编排 RAG 流程，没有依赖 LangChain 执行主链路。

## 角色

- `operator`：问答、创建工单、查看自己的工单、确认或退回专家方案。
- `expert`：领取工单、提交方案、查看知识库、将完成方案录入 FAQ。
- `admin`：管理账号、FAQ、全部工单和统计数据。

只有 `operator` 可以发起问答和创建工单。

## 核心目录

```text
backend/                         FastAPI 后端与 RAG 引擎
frontend/                        Vue 前端源码
knowledge_base/                  生成后的知识库 JSON
FAQ_1000条.json                  原项目历史模拟 FAQ
backend/scripts/build_ops_faq_kb.py
                                 FAQ 生成、合并、导入与向量重建脚本
start.bat / start.sh             本地启动脚本
```

`backend/data`、`frontend/dist`、`node_modules`、`venv` 和日志均为本地运行产物，不提交 Git。

## 知识库

- `official_ops_faq_1000.json`：基于 Linux、Docker、Kubernetes、Nginx、Apache、MySQL、PostgreSQL、Redis，以及阿里云、华为云、腾讯云故障文档构造的 1000 条可追溯 FAQ。
- `merged_ops_faq_2000.json`：与历史 FAQ 去重后的 1985 条导入数据。

FAQ 是由预设故障场景和提问模板构造，并附有来源 URL；它不是对 1000 篇官方网页的逐篇抓取。

## Windows 初始化

```powershell
cd "C:\path\to\enterprise-knowledge-rag"

python -m venv venv
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt

cd frontend
npm.cmd ci
npm.cmd run build
cd ..

ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

首次启动后端会创建数据库、管理员账号和种子 FAQ：

```powershell
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 5173
```

默认管理员为 `admin / 123456`。首次启动完成后，可停止服务并导入完整知识库：

```powershell
cd backend
..\venv\Scripts\python.exe scripts\build_ops_faq_kb.py --import-db --reindex
```

再次启动后访问 `http://127.0.0.1:5173`。
