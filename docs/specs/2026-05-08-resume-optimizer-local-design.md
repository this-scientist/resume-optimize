# 本地简历优化助手 — 产品设计规格

**日期**：2026-05-08  
**状态**：已定稿（头脑风暴输出）  
**技术选型**：方案 1 — Python FastAPI + SQLite + 向量库 + Vite/React 前端

---

## 1. 背景与目标

构建在本机运行的 **简历优化 Web 应用**（浏览器访问 `localhost`），聚合三类输入：

1. **面试经验 / 笔记**：用户提供网页 URL，经用户确认后以轻量 HTTP 抓取正文，分块后通过 **Embedding API** 写入本地向量库；亦支持用户直接撰写笔记。
2. **简历初稿**：Markdown 编写，支持多份简历的列表管理。
3. **招聘岗位**：以招聘页 URL 为主进行轻量抓取获取 JD；失败则 **粘贴 JD 全文** 兜底。岗位可关联一份简历，并维护 **完全自定义** 的面试进度阶段。

**一键简历优化**：结合 **岗位 JD 全文**（优先直接进上下文）、**向量检索得到的面试相关知识片段**、**当前简历全文**，调用用户配置的国内可访问 **Chat API**（OpenAI 兼容：DeepSeek、ChatGLM、通义千问、Mimo 等），生成优化结果。

---

## 2. 范围与非目标

### 2.1 范围内（第一版）

- 单用户、本地数据落盘；服务绑定 **127.0.0.1**，无 Token/密码鉴权（个人设备场景）。
- 面试笔记 URL：轻量 HTTP（`GET` + HTML 解析 / 正文抽取），**不含**无头浏览器默认路径。
- Embedding 与 Chat 均走用户配置的 **云端 API**（用户自备 Key 与 Base URL）。
- 三大模块：**面试知识库**、**简历管理**（含分类归档）、**招聘岗位**（关联简历 + 自定义面试阶段）。
- 简历 **分类**（如互联网 / 国企银行 / 外企）：仅用于 **筛选与归档**，**不自动改变**默认优化提示词；优化侧重点由 **JD** 与用户在单次优化中的补充说明主导。

### 2.2 非目标（第一版不做）

- 多租户、云端同步、账号体系。
- 登录墙后页面抓取、绕过 robots/付费墙、对第三方站点的合规自动化裁决。
- 默认无头浏览器抓取（若未来需要，可作为独立「深度抓取」扩展）。

---

## 3. 总体架构

### 3.1 运行形态

- 单一 **Python 进程**：**FastAPI** 提供 REST API；生产式本地运行时可 **托管** 前端构建产物（静态文件）。开发期前后端可分端口，由 Vite 代理 API。
- 仅监听 **127.0.0.1**。

### 3.2 逻辑分层

- **API 层**：请求校验、超时；不对本地访问做鉴权。
- **领域层**：简历、岗位、面试来源、面试流水线与阶段、一键优化编排（组装上下文 → 调用模型 → 持久化新版本）。
- **基础设施层**：SQLite、向量库、HTTP 客户端（抓取）、Embedding/Chat 客户端（OpenAI 兼容）。

### 3.3 向量检索策略（已定）

- **向量库主要索引「面试知识」**（URL 确认后的笔记正文、用户手写笔记）。
- **JD 优先以全文形式加入 Chat 上下文**（通常长度可控）；若超长则 **截断或先摘要再入上下文**，**不把 JD 作为默认向量检索主路径**，以降低调试复杂度与检索噪声。

---

## 4. 数据模型与存储

### 4.1 用户数据目录

- 约定单一 **用户数据根目录**（macOS 可默认 `~/Library/Application Support/<AppName>/`，具体名称在实现时确定）；支持环境变量覆盖。SQLite、向量库持久化目录、配置均置于此，便于 **整目录备份**。

### 4.2 SQLite 实体

| 实体 | 说明 |
|------|------|
| `resume` | 简历：`title`、`category`（枚举或自由文本）、`current_body_md`、`created_at`、`updated_at`。 |
| `resume_revision` | 版本：`resume_id`、`body_md`、`source`（`user_edit` \| `optimize`）、`created_at`；可选 `job_id`。默认：**一键优化产生新版本**，并 **更新** `resume.current_body_md` 为该版本；支持回滚到历史 revision。 |
| `job_posting` | 岗位：`company`、`title`、`jd_source_url`（可空）、`jd_text`（必填）、`resume_id`（FK，可空）、`jd_fetch_status`（`ok` \| `failed`）、时间戳。抓取失败必须允许用户 **粘贴** 更新 `jd_text`。 |
| `interview_pipeline` | 与 `job_posting` **1:1**（或 `job_posting.pipeline_id`）。 |
| `pipeline_stage` | `pipeline_id`、`name`、`sort_order`；阶段 **完全由用户自定义**。 |
| `job_stage_state` | 实现可选用「当前阶段指针 + 各阶段完成标记」的简化模型；细节以实现为准，需支持阶段列表编辑与推进。 |
| `interview_source` | `kind`：`url` \| `manual_note`；`url`、标题、抓取或手写正文、`fetch_status`。 |
| `optimization_run`（可选） | 审计：`resume_id`、`job_id`、`model`、错误信息、耗时；避免在日志中保存完整 API Key。 |

### 4.3 向量 chunk metadata

- `source_type`：`interview_url` \| `interview_note`（JD 默认不向量化入库）。
- `source_id`：对应 `interview_source.id`。
- `chunk_index`、`created_at`。
- 单用户可不使用 `user_id`；预留无损。

### 4.4 一致性

- 删除或重建某 `interview_source` 时：按 **source 粒度** 删除或失效对应向量 chunk 后重建索引。
- `jd_text` 变更：不改变面试知识向量；优化时始终读取最新 `jd_text`。

---

## 5. 核心流程与 API 概要

### 5.1 面试知识库

- `POST /api/interview-sources`（URL）：抓取 → 预览 → 用户 **`POST .../{id}/confirm`** 后分块、Embedding、入库。
- 手动笔记：`POST` 直接提交正文。
- `GET` 列表与详情；`DELETE` 同步删向量。
- 可选：`POST .../{id}/reindex`（正文变更后）。

### 5.2 简历管理

- `GET/POST /api/resumes`，`GET/PATCH/DELETE /api/resumes/{id}`。
- `GET /api/resumes/{id}/revisions`，`POST .../revisions/{rid}/restore`。
- `POST /api/resumes/{id}/optimize`：body 含 `job_id`（推荐必填）、可选 `top_k`、用户补充说明。服务端：**JD 全文 + Top-K 面试片段 + 当前简历** → Chat → 新版本 + 更新当前稿。

### 5.3 招聘岗位

- `POST /api/jobs`：填 `jd_source_url` 时尝试抓取；写入 `jd_text` 与 `jd_fetch_status`。
- `PATCH /api/jobs/{id}`：关联 `resume_id`、修正 `jd_text`。
- `PUT /api/jobs/{id}/pipeline`：有序阶段列表；`PATCH` 阶段状态（实现可合并端点）。

### 5.4 模型设置

- `GET/PUT /api/settings/models`：Chat 与 Embedding 各自的 `base_url`、`api_key`、`model_name`（仅存本机；首版可明文存本地配置并在文档中声明风险）。
- 提供 DeepSeek / ChatGLM / Qwen / Mimo 等 **文档链接与默认 Base URL 占位**，由用户填写 Key。

### 5.5 前端路由（建议）

- `/knowledge`、`/resumes`、`/resumes/:id`、`/jobs`、`/jobs/:id`、`/settings`。

---

## 6. 错误处理与非功能需求

### 6.1 抓取

- 超时（默认建议 15–30s，可配置）、非 2xx、非 HTML、正文过短：返回明确错误，UI 提供 **粘贴正文**。
- UI 固定展示 **合规与版权免责声明**（用户自负）。

### 6.2 模型调用

- Chat / Embedding 分别设置超时；Embedding 批量失败时标记来源 **index_failed**，允许重试。
- **禁止**在日志中输出完整 API Key。

### 6.3 隐私说明

- 设置页说明：优化与建索引会向 **用户选择的 API 服务商** 发送相应文本；结构化数据与向量库仍主要保存在本机。

### 6.4 性能

- 检索默认 Top-K（建议 6–12）；对简历与 JD 做 **token 预算**，必要时截断检索片段（保留高相关 chunk）。
- 数据目录避免放在网络同步盘上。

### 6.5 备份

- 备份方式：**复制整个用户数据目录**。

---

## 7. 测试策略

- **单元测试**：正文抽取、分块、prompt 组装等纯函数。
- **集成测试**：FastAPI `TestClient` + 临时目录 SQLite + 向量库 mock 或临时实例。
- **手工冒烟**：抓取失败兜底、优化生成新版本、岗位关联简历、流水线阶段编辑。

---

## 8. 开放项（实现阶段细化）

- 向量库具体选型（Chroma 持久化 / LanceDB 等）与 Python 依赖锁定。
- `pipeline_stage` 与状态机的最简 UI 模型（指针 vs 看板）。
- 具体分块大小、重叠与中文分句策略。
- macOS 以外平台的用户数据目录约定。

---

## 9. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-08 | 初版：头脑风暴定稿 |
