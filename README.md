# Resume Optimizer（本地版）

在 `127.0.0.1` 运行的简历优化 Web：FastAPI + SQLite + Chroma + Vite/React。支持面试笔记入库、多简历 Markdown、岗位 JD、流水线阶段与一键优化。

## 环境要求

- Python 3.11+
- Node.js 18+（用于前端构建与开发）

## 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir .
```

健康检查：<http://127.0.0.1:8000/api/health>

### 环境变量（可选）

前缀均为 `RESUME_OPTIMIZER_`，例如：

- `DATA_DIR`：数据目录（默认按操作系统用户目录）
- `EMBEDDING_API_KEY` / `EMBEDDING_MODEL` / `EMBEDDING_BASE_URL`
- `CHAT_API_KEY` / `CHAT_MODEL` / `CHAT_BASE_URL`

也可以在界面 **设置** 页写入 `settings.json`（与数据目录同级）。

## 前端

```bash
cd frontend
npm install
npm run dev
```

开发时代理：`/api` → `http://127.0.0.1:8000`（见 `vite.config.ts`）。请先启动后端。

生产构建：`npm run build`，静态资源在 `frontend/dist/`。

## 数据与备份

- SQLite：`$DATA_DIR/app.sqlite3`
- Chroma：`$DATA_DIR/chroma/`
- 设置：`$DATA_DIR/settings.json`

备份时复制整个数据目录即可。

升级后端后若 SQLite 出现「缺少列」类错误，可**关闭应用后删除** `app.sqlite3` 再启动（会清空本地库表数据；Chroma 如需一致可一并删掉 `chroma` 目录）。

## 手动冒烟（建议）

1. **设置**：填写 Chat 与 Embedding 的模型与 Key（或仅用环境变量）。
2. **面试知识**：笔记或 URL → 预览 → 确认建索引（Embedding 需可用）。
3. **岗位**：新建岗位；若 URL 抓取失败，在详情页粘贴 JD。
4. **简历**：编辑 Markdown → 关联岗位 → **一键优化** 生成新版本。
5. **流水线**：岗位详情中编辑阶段行；查看当前阶段 ID。

## 测试（后端）

```bash
cd backend
source .venv/bin/activate
pytest -q
```

## 许可证

MIT（若未另行指定，以仓库内 LICENSE 为准）。
