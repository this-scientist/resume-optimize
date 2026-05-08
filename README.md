# Resume Optimizer（本地版）

在 `127.0.0.1` 运行的简历优化 Web 应用：FastAPI 后端 + Vite/React 前端，数据落 SQLite 与 Chroma，支持面试知识入库、多份简历 Markdown、岗位 JD、流水线阶段与**一键优化**（后台多阶段 LLM 编排，对用户单入口）。

---

## 依赖环境

| 部分 | 说明 |
|------|------|
| **Python** | 见仓库根目录 [`requirements.txt`](./requirements.txt)（含 pytest，与当前开发机 `pip freeze` 一致；**含 torch 等大包**，换平台时若安装失败可仅装 `backend/pyproject.toml` 中的直接依赖后由 pip 解析）。 |
| **Node.js** | 18+，前端依赖见 [`frontend/package.json`](./frontend/package.json)，锁定安装可用 [`frontend/package-lock.json`](./frontend/package-lock.json)。 |

推荐后端安装方式（任选其一）：

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r ../requirements.txt
```

或从源码元数据安装（不锁定传递依赖版本）：

```bash
cd backend && pip install -e ".[dev]"
```

前端：

```bash
cd frontend && npm ci   # 或 npm install
```

一键脚本（根目录执行）：

```bash
chmod +x scripts/*.sh    # 仅需首次
./scripts/setup-dev.sh
```

---

## 启动方式

需要先启动 **后端**，再启动 **前端**（开发模式下前端通过 Vite 代理访问 `/api`）。

### 方式 A：脚本（推荐）

在项目根目录：

```bash
./scripts/start-backend.sh
```

另开终端：

```bash
./scripts/start-frontend.sh
```

### 方式 B：手动命令

**后端**（工作目录须在 `backend`，以便加载包 `app`）：

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir .
```

健康检查：<http://127.0.0.1:8000/api/health>

**前端**：

```bash
cd frontend
npm run dev
```

浏览器访问终端输出的本地地址（通常为 <http://127.0.0.1:5173>）。`/api` 会代理到 `http://127.0.0.1:8000`（见 `frontend/vite.config.ts`）。

**生产构建前端**：`cd frontend && npm run build`，静态资源输出到 `frontend/dist/`。

---

## 技术实现概要

### 总体架构

- **单体后端**：单进程 FastAPI，SQLite 存结构化业务数据（简历、岗位、面试来源、流水线等）。
- **向量检索**：面试笔记/网页摘录经分块后，用本地 **[FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding)（BGE）** 嵌入，写入 **Chroma** 持久化集合 `interview_knowledge`；与用户查询向量做相似度检索。
- **大模型调用**：通过 **OpenAI 兼容 API**（`openai` 库）完成对话与补全；配置项为 Chat 的 `base_url` / `api_key` / `model`（与 Embedding 解耦，Embedding 为本地模型名）。

### 后端目录与职责（`backend/app/`）

| 模块 | 作用 |
|------|------|
| `api/routes/` | HTTP 路由：健康检查、面试来源、简历、岗位、设置等。 |
| `db/models.py` | SQLAlchemy 模型（简历、岗位、面试来源、流水线等）。 |
| `services/embeddings.py` | `FlagModel`：`encode_corpus` 建索引，`encode_queries` 检索；中文模型默认检索指令见 FlagEmbedding 文档。 |
| `services/chroma_store.py` | Chroma 持久化；**按当前嵌入模型名分集合**（`interview_knowledge__<模型名>`），避免不同向量维度混写；旧数据可能在固定名 `interview_knowledge`；`InterviewSource.embedding_model` 记录建索引用模型。 |
| `services/interview_index.py` | 将某条 `InterviewSource` 正文分块、嵌入并写入 Chroma。 |
| `services/optimize_resume.py` | 一键优化入口：拉 JD、简历，检索面试片段，调用下游图编排。 |
| `services/optimize_graph.py` | **LangGraph** 线性四节点流水线（对用户不可见）：JD 结构化拆解 → 人岗差距分析 → 简历重写 → 面试钩子融合；每步一次 `complete_chat`，最终产出 Markdown 简历正文。 |
| `services/chat_models.py` | OpenAI 兼容 `chat.completions` 封装。 |
| `services/settings_file.py` | 读写数据目录下的 `settings.json`，与 `config.py` 环境变量合并。 |

### 一键优化数据流（简化）

1. 根据简历正文（或 JD 摘要）做 **query 嵌入**，从 Chroma 取 Top-K 面试知识片段（长度经 `token_budget` 裁剪）。
2. 将 JD、片段、简历与可选「额外说明」传入 **LangGraph**，顺序执行四阶段 LLM，返回**一条**最终简历字符串。
3. 写入 `resume_revisions` 并更新 `resumes.current_body_md`。

### 前端（`frontend/src/`）

- **React Router**：简历列表/编辑、岗位列表/详情、面试知识列表/导入/粘贴/详情、设置页等。
- **API**：`src/api/client.ts` 使用 `VITE_API_BASE`（可选）；开发时依赖 Vite 代理 `/api`。

### 数据与备份

| 路径 | 内容 |
|------|------|
| `$DATA_DIR/app.sqlite3` | SQLite（`DATA_DIR` 默认按操作系统用户目录，前缀环境变量 `RESUME_OPTIMIZER_`） |
| `$DATA_DIR/chroma/` | Chroma 向量数据（多集合；与嵌入模型绑定） |
| `$DATA_DIR/settings.json` | 界面保存的模型与 Key（掩码展示） |

备份：复制整个 `$DATA_DIR` 即可。升级若遇表结构问题，可在停服后备份再重建库。**更换嵌入模型**时：新版本已按模型自动分集合，一般无需手删整个 `chroma`；若仍报维度错误，可停服后删除 `chroma` 目录并在应用内对面试来源**重新确认建索引**。

---

## 环境变量（可选）

### `.env` 加载顺序

1. **仓库根目录** `.env`（推荐）  
2. **`backend/.env`**  

启动时还会 `load_dotenv`（非 pytest 场景），以便 **`LANGSMITH_*`** 等未映射到 `Settings` 的变量进入 `os.environ`，供 LangChain / LangGraph 使用。

### `RESUME_OPTIMIZER_*` 前缀（标准）

| 变量 | 含义 |
|------|------|
| `DATA_DIR` | 数据目录（完整变量名为 `RESUME_OPTIMIZER_DATA_DIR`） |
| `HOST` / `PORT` | HTTP 监听（默认 `127.0.0.1:8000`） |
| `DB_MODE` | 数据库模式，当前仅使用 `local`（SQLite） |
| `EMBEDDING_MODEL` | 本地 BGE 模型名（默认 `BAAI/bge-small-zh-v1.5`） |
| `EMBEDDING_USE_FP16` | 是否 FP16 推理（默认 true） |
| `CHAT_API_KEY` / `CHAT_MODEL` / `CHAT_BASE_URL` | OpenAI 兼容 Chat 接口 |

`EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL` 已不再参与本地向量计算，仅兼容设置表单。

### 无前缀别名（在对应 `RESUME_OPTIMIZER_*` 未设置时作为后备）

| 后备变量 | 映射到 |
|----------|--------|
| `OPENAI_API_KEY` / `GLM_API_KEY` | Chat API Key |
| `OPENAI_BASE_URL` / `GLM_BASE_URL` / `OPENAI_API_BASE` | Chat Base URL |
| `OPENAI_MODEL` / `GLM_MODEL` | Chat 模型名 |
| `UVICORN_HOST` / `UVICORN_PORT` | 监听地址与端口 |
| `DB_MODE` | 与 `RESUME_OPTIMIZER_DB_MODE` 相同语义 |

也可在界面 **设置** 写入 `settings.json`；若某项在 JSON 中非空，则优先于环境默认值（见 `user_config.effective_*`）。

---

## 手动冒烟（建议）

1. **设置**：配置 Chat；Embedding 填写 Hugging Face 上的 BGE 模型名。
2. **面试知识**：URL 或粘贴笔记 → 预览 → 确认建索引。
3. **岗位**：新建岗位并确保有 JD 文本。
4. **简历**：编辑 Markdown → 关联岗位 → **一键优化**。
5. **流水线**：在岗位详情维护阶段（若使用）。

---

## 测试（后端）

```bash
cd backend
source .venv/bin/activate
pytest -q
```

---

## 许可证

MIT（若未另行指定，以仓库内 LICENSE 为准）。
