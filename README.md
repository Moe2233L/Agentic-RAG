# AgenticRAG — 企业级智能问答系统 🧠

基于 FastAPI + Vue 3 + LangGraph + ChromaDB 构建的企业级 RAG（检索增强生成）问答系统。支持知识库管理、多源检索、知识图谱推理、联网搜索与深度 Agent 推理，通过 SSE 实时流式输出回答。

## 功能特性 ✨

- **📚 知识库管理** — 创建/删除/上传/索引，全生命周期管理
- **🔍 语义检索** — BGE-M3 稠密向量 + Cross-encoder 重排，精准匹配
- **🌐 联网搜索** — Tavily 实时 Web 查询，联网信息兜底
- **🕸️ 知识图谱** — LLM 自动抽取实体关系 + Neo4j 存储 + d3 可视化
- **🧠 深度 Agent** — LangGraph 多步推理路由，复杂问题拆解
- **⚡ 流式对话** — SSE 实时推送，逐 token 输出
- **🔒 安全渲染** — DOMPurify 净化 Markdown，XSS 防护
- **🔄 对话历史** — 自动保存上下文，支持连续追问

## 技术栈 📋

| 层级    | 技术                                    |
| ----- | ------------------------------------- |
| 后端框架  | FastAPI + Uvicorn                     |
| AI 框架 | LangChain + LangGraph                 |
| 大语言模型 | OpenAI 兼容                             |
| 向量库   | ChromaDB（BGE-M3 嵌入 + BGE-reranker 重排） |
| 图数据库  | Neo4j                                 |
| 联网搜索  | Tavily API                            |
| 前端框架  | Vue 3 + TypeScript                    |
| 构建工具  | Vite                                  |
| 图谱可视化 | d3.js forceSimulation                 |
| 流式通信  | SSE（sse-starlette）                    |

## 架构概览 🏗️

![系统架构概览](Architecture%20Overview.jpg)

## 系统流程 🔄

![系统流程图](Flow%20Chart.jpg)

## 快速开始 🚀

### 前置条件

- Python 3.11+
- Node.js 18+
- OpenAI API Key（或兼容的第三方服务）
- Neo4j 数据库（可选，图谱功能需要）

### 1. 安装后端

```bash
pip install -r backend/requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入配置：

```env
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

TAVILY_API_KEY=tvly-xxx

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

HOST=0.0.0.0
PORT=8000
```

> ⚠️ `.env` 文件包含敏感 API 密钥，已默认加入 `.gitignore`。请勿手动将其加入版本控制。

### 3. 启动后端

```bash
python -m backend.src.main
# 终端输出: Uvicorn running on http://0.0.0.0:8000
```

验证后端：

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### 4. 安装并启动前端

```bash
cd frontend
npm install
npm run dev
# 终端输出: Local: http://localhost:5173
```

### 5. 使用

打开浏览器访问 `http://localhost:5173`，创建知识库 → 上传文档 → 索引 → 开始问答。

## 使用指南 📖

| 步骤 | 操作    | 说明                                |
| -- | ----- | --------------------------------- |
| 1  | 创建知识库 | 侧边栏点击「+ 新建」，输入名称和描述               |
| 2  | 上传文档  | 支持 PDF / Word / Excel / PPT / 纯文本 |
| 3  | 索引文档  | 上传后点击「索引」，自动切片+向量化                |
| 4  | 开启聊天  | 输入问题，可选联网/深度模式                    |
| 5  | 查看图谱  | 构建知识图谱后，可视化查看实体关系                 |
| 6  | 追问    | 基于对话历史自然延续                        |

## 项目结构 📁

```
AgenticRAG/
├── backend/
│   ├── Dockerfile                    # 后端容器镜像
│   └── src/
│       ├── main.py                   # FastAPI 应用入口 + SSE 端点
│       ├── config.py                 # 环境配置加载（.env → Settings）
│       ├── models.py                 # Pydantic 数据模型
│       ├── constants.py              # 常量定义
│       ├── agent/
│       │   └── orchestrator.py       # LangGraph Agent 编排器
│       ├── rag/
│       │   ├── embedder.py           # BGE-M3 嵌入模型封装
│       │   ├── retriever.py          # 检索器（稠密 + 重排）
│       │   ├── store.py              # ChromaDB 向量存储
│       │   └── loader.py             # 文档加载器
│       ├── services/
│       │   ├── index_service.py      # 索引服务
│       │   ├── kb_service.py         # 知识库管理服务
│       │   ├── graph_service.py      # Neo4j 图服务
│       │   └── sse_manager.py        # SSE 事件管理
│       ├── tools/
│       │   └── extraction_tool.py    # 实体关系抽取工具
│       └── utils/
│           └── helpers.py            # 公共工具函数
├── frontend/
│   └── src/
│       ├── main.ts                   # Vue 应用入口
│       ├── App.vue                   # 根组件
│       ├── style.css                 # 全局样式 + CSS 变量
│       ├── stores/
│       │   └── chat.ts               # 会话状态管理
│       ├── utils/
│       │   ├── sse.ts                # SSE 流解析
│       │   └── kb.ts                 # 知识库 API 封装
│       ├── types/
│       │   └── research.ts           # TypeScript 类型定义
│       ├── views/
│       │   ├── HomeView.vue          # 聊天主页
│       │   ├── KBView.vue            # 知识库管理页
│       │   └── GraphView.vue         # 图谱可视化页
│       └── components/
│           └── MarkdownViewer.vue    # Markdown 安全渲染
├── data/
│   ├── chroma/                       # ChromaDB 向量数据
│   └── knowledge_bases/
│       ├── _meta.json                # 知识库元数据
│       └── {kb_id}/
│           ├── documents/            # 上传的文档
│           └── graph.json            # 图谱数据
├── .env.example                      # 环境变量模板
├── .gitignore                        # Git 忽略规则
├── requirements.txt                  # Python 依赖清单
└── README.md
```

## API 文档 📡

### GET `/health`

健康检查。

**响应：**

```json
{"status": "ok"}
```

### POST `/query`

问答请求（非流式）。

**请求体：**

```json
{
  "question": "年假几天",
  "use_web": false,
  "deep_mode": false,
  "conversation_id": ""
}
```

**参数说明：**

| 参数                | 类型      | 默认值   | 说明            |
| ----------------- | ------- | ----- | ------------- |
| `question`        | string  | -     | 问题内容，必填       |
| `use_web`         | boolean | false | 启用联网搜索        |
| `deep_mode`       | boolean | false | 启用深度 Agent 推理 |
| `conversation_id` | string  | ""    | 对话 ID，续传上下文   |

### POST `/query/stream`

问答请求（SSE 流式输出）。请求体同 `/query`，返回 `EventSource` 流，事件类型：

| 事件       | 说明                 |
| -------- | ------------------ |
| `start`  | 会话开始，携带 `sid`      |
| `status` | 阶段状态（检索中… / 生成回答…） |
| `token`  | 生成文本片段             |
| `done`   | 回答完成，携带完整回答 + 证据   |
| `error`  | 错误信息               |

### 知识库 API

| 方法     | 路径                                              | 说明     |
| ------ | ----------------------------------------------- | ------ |
| POST   | `/knowledge-bases`                              | 创建知识库  |
| GET    | `/knowledge-bases`                              | 知识库列表  |
| DELETE | `/knowledge-bases/{kb_id}`                      | 删除知识库  |
| POST   | `/knowledge-bases/{kb_id}/upload`               | 上传文档   |
| GET    | `/knowledge-bases/{kb_id}/documents`            | 文档列表   |
| DELETE | `/knowledge-bases/{kb_id}/documents/{filename}` | 删除文档   |
| POST   | `/knowledge-bases/{kb_id}/index`                | 索引文档   |
| POST   | `/knowledge-bases/{kb_id}/graph/build`          | 构建知识图谱 |
| GET    | `/knowledge-bases/{kb_id}/graph`                | 获取图谱数据 |
| DELETE | `/knowledge-bases/{kb_id}/graph`                | 删除图谱   |
| GET    | `/knowledge-bases/index/status`                 | 索引状态统计 |

## 配置参考 ⚙️

所有配置项通过项目根目录下的 `.env` 文件加载：

| 环境变量                | 默认值                         | 说明                |
| ------------------- | --------------------------- | ----------------- |
| `OPENAI_API_KEY`    | -                           | OpenAI API 密钥（必填） |
| `OPENAI_API_BASE`   | `https://api.openai.com/v1` | API 基础地址          |
| `LLM_MODEL`         | `gpt-4o-mini`               | 模型名称              |
| `TAVILY_API_KEY`    | -                           | Tavily 搜索 API 密钥  |
| `NEO4J_URI`         | `bolt://localhost:7687`     | Neo4j 连接地址        |
| `NEO4J_USER`        | `neo4j`                     | Neo4j 用户名         |
| `NEO4J_PASSWORD`    | `password`                  | Neo4j 密码          |
| `BGE_MODEL_PATH`    | `BAAI/bge-m3`               | 嵌入模型路径            |
| `BGE_RERANKER_PATH` | `BAAI/bge-reranker-v2-m3`   | 重排模型路径            |
| `HOST`              | `0.0.0.0`                   | 服务监听地址            |
| `PORT`              | `8000`                      | 服务端口              |

## Docker 部署 🐳

一键启动后端 + Neo4j：

```bash
docker compose up -d
```

包含两个服务：

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| `backend` | 本地构建 | `8000` | FastAPI 应用 |
| `neo4j` | `neo4j:5-community` | `7474`(UI) `7687`(bolt) | 知识图谱库 |

**数据持久化**：
- `./data/` → 向量库 + 文档持久化到宿主机
- `hf_cache` volume → BGE 模型缓存，重启不重下
- `neo4j_data` volume → Neo4j 数据库持久化

> ⚠️ 首次启动需联网下载 BGE-M3 模型（~2.2GB），后续使用缓存。

## 本地开发 🛠️

### 热重载开发

```bash
# 终端 1：后端（热重载）
uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2：前端（HMR + API 代理）
cd frontend && npm run dev
```

### 构建前端生产版本

```bash
cd frontend
npm run build
# 产出在 frontend/dist/
```

## 注意事项 ⚠️

- **首次启动** 自动下载 BGE-M3 嵌入模型（\~2.2GB），模型缓存到 `~/.cache/huggingface/hub/`
- **网络环境**：如果无法访问 HuggingFace，设置环境变量 `HF_HUB_OFFLINE=1` 使用本地缓存
- **Neo4j**：知识图谱功能需要 Neo4j 数据库，不启用不影响基础问答
- **数据文件**：上传的文档存储在 `data/knowledge_bases/` 目录

## License 📄

MIT
