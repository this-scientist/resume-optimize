import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiGet, apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";

type Job = {
  id: number;
  company: string;
  title: string;
  salary: string;
  published_at: string | null;
  jd_source_url: string | null;
  jd_text: string;
  jd_fetch_status: string;
  resume_id: number | null;
  current_stage_id: number | null;
};

type Resume = { id: number; title: string };

function toDateInputValue(iso: string | null): string {
  if (!iso) return "";
  // 使用日期段，避免带 T 的 ISO 被按 UTC 解析后错一天
  const m = /^(\d{4}-\d{2}-\d{2})/.exec(iso);
  if (m) return m[1];
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${mo}-${day}`;
}

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const jid = Number(id);
  const [job, setJob] = useState<Job | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [stages, setStages] = useState("笔试\n一面\n二面");
  const [err, setErr] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [company, setCompany] = useState("");
  const [title, setTitle] = useState("");
  const [salary, setSalary] = useState("");
  const [publishedDate, setPublishedDate] = useState("");
  const [jdSourceUrl, setJdSourceUrl] = useState("");
  const [fetchStatus, setFetchStatus] = useState<"ok" | "failed">("failed");
  const [jdText, setJdText] = useState("");
  const [resumeId, setResumeId] = useState<number | "">("");
  const [currentStageId, setCurrentStageId] = useState<number | "">("");

  useEffect(() => {
    void (async () => {
      try {
        const j = await apiGet<Job>(`/api/jobs/${jid}`);
        setJob(j);
        setCompany(j.company);
        setTitle(j.title);
        setSalary(j.salary);
        setPublishedDate(toDateInputValue(j.published_at));
        setJdSourceUrl(j.jd_source_url ?? "");
        setFetchStatus(j.jd_fetch_status === "ok" ? "ok" : "failed");
        setJdText(j.jd_text);
        setResumeId(j.resume_id ?? "");
        setCurrentStageId(j.current_stage_id ?? "");
        const rs = await apiGet<Resume[]>("/api/resumes/");
        setResumes(rs);
      } catch (e) {
        setErr(String(e));
      }
    })();
  }, [jid]);

  function publishedAtPayload(): string | null {
    if (!publishedDate.trim()) return null;
    // 仅传 YYYY-MM-DD，由后端解析为当天 0 点（无时区歧义）
    return publishedDate.trim();
  }

  async function saveJobFields() {
    setErr(null);
    setOkMsg(null);
    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        company,
        title,
        salary,
        published_at: publishedAtPayload(),
        jd_text: jdText,
        jd_source_url: jdSourceUrl.trim() || null,
        jd_fetch_status: fetchStatus,
        resume_id: resumeId === "" ? null : resumeId,
        current_stage_id: currentStageId === "" ? null : currentStageId,
      };
      const updated = await apiSend<Job>(`/api/jobs/${jid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      setJob(updated);
      setCompany(updated.company);
      setTitle(updated.title);
      setSalary(updated.salary);
      setPublishedDate(toDateInputValue(updated.published_at));
      setJdSourceUrl(updated.jd_source_url ?? "");
      setFetchStatus(updated.jd_fetch_status === "ok" ? "ok" : "failed");
      setJdText(updated.jd_text);
      setResumeId(updated.resume_id ?? "");
      setCurrentStageId(updated.current_stage_id ?? "");
      setOkMsg("已保存");
      window.setTimeout(() => setOkMsg(null), 2500);
    } catch (e) {
      setErr(String(e));
    } finally {
      setSaving(false);
    }
  }

  async function savePipeline() {
    setErr(null);
    setOkMsg(null);
    const list = stages
      .split(/\r?\n/)
      .map((s) => s.trim())
      .filter(Boolean);
    try {
      const updated = await apiSend<Job>(`/api/jobs/${jid}/pipeline`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stages: list }),
      });
      setJob(updated);
      setCurrentStageId(updated.current_stage_id ?? "");
      setOkMsg("流水线已更新");
      window.setTimeout(() => setOkMsg(null), 2500);
    } catch (e) {
      setErr(String(e));
    }
  }

  if (!job) {
    return (
      <div className="page">
        {err ? <p className="err">{err}</p> : <p>加载中…</p>}
        <Disclaimer />
      </div>
    );
  }

  return (
    <div className="page job-detail-page">
      <p>
        <Link to="/jobs">← 列表</Link>
      </p>
      <h1>
        {(title || company).trim()
          ? [company, title].filter(Boolean).join(" — ")
          : `岗位 #${jid}`}
      </h1>
      <p className="job-detail-page__lede">
        爬取结果可能不完整，可在下方逐项修正；保存后一键优化与列表展示均使用此处数据。
      </p>
      {err ? (
        <p className="err" role="alert">
          {err}
        </p>
      ) : null}
      {okMsg ? (
        <p className="job-detail-page__ok" role="status">
          {okMsg}
        </p>
      ) : null}

      <div className="card job-detail-edit">
        <h2 className="resume-list-page__section-title">职位信息</h2>
        <div className="job-detail-form">
          <div className="job-detail-form__field">
            <label htmlFor="job-co">公司</label>
            <input
              id="job-co"
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              autoComplete="organization"
            />
          </div>
          <div className="job-detail-form__field">
            <label htmlFor="job-ti">职位名称</label>
            <input
              id="job-ti"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div className="job-detail-form__field">
            <label htmlFor="job-sal">薪资</label>
            <input
              id="job-sal"
              type="text"
              placeholder="如：25-35万/年、面议"
              value={salary}
              onChange={(e) => setSalary(e.target.value)}
            />
          </div>
          <div className="job-detail-form__field">
            <label htmlFor="job-pub">发布时间</label>
            <input
              id="job-pub"
              type="date"
              value={publishedDate}
              onChange={(e) => setPublishedDate(e.target.value)}
            />
            <span className="resume-list-page__hint">
              留空表示未填写或清除解析日期
            </span>
          </div>
          <div className="job-detail-form__field job-detail-form__field--full">
            <label htmlFor="job-url">JD 页面 URL</label>
            <input
              id="job-url"
              type="url"
              placeholder="https://"
              value={jdSourceUrl}
              onChange={(e) => setJdSourceUrl(e.target.value)}
            />
          </div>
          <div className="job-detail-form__field">
            <label htmlFor="job-fs">抓取状态（手工）</label>
            <select
              id="job-fs"
              value={fetchStatus}
              onChange={(e) =>
                setFetchStatus(e.target.value as "ok" | "failed")
              }
            >
              <option value="failed">失败 — 内容多为手动粘贴</option>
              <option value="ok">成功 — 正文来自页面抓取</option>
            </select>
          </div>
          <div className="job-detail-form__field">
            <label htmlFor="job-res">关联简历</label>
            <select
              id="job-res"
              value={resumeId === "" ? "" : String(resumeId)}
              onChange={(e) =>
                setResumeId(e.target.value ? Number(e.target.value) : "")
              }
            >
              <option value="">未关联</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title || `#${r.id}`}
                </option>
              ))}
            </select>
          </div>
          <div className="job-detail-form__field">
            <label htmlFor="job-stage">当前阶段 ID</label>
            <input
              id="job-stage"
              type="number"
              min={1}
              step={1}
              placeholder="保存流水线后填写"
              value={currentStageId === "" ? "" : currentStageId}
              onChange={(e) => {
                const v = e.target.value;
                setCurrentStageId(v === "" ? "" : Number(v));
              }}
            />
            <span className="resume-list-page__hint">
              与下方流水线阶段对应；不确定可留空
            </span>
          </div>
          <div className="job-detail-form__field job-detail-form__field--full">
            <label htmlFor="jd-body">JD 正文</label>
            <textarea
              id="jd-body"
              rows={14}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="抓取失败时在此粘贴完整 JD；一键优化依赖此正文。"
            />
          </div>
        </div>
        <div className="job-detail-edit__actions">
          <button
            type="button"
            className="primary"
            onClick={() => void saveJobFields()}
            disabled={saving}
            aria-busy={saving}
          >
            {saving ? "保存中…" : "保存职位与 JD"}
          </button>
        </div>
      </div>

      <div className="card">
        <h2 className="resume-list-page__section-title">面试流水线</h2>
        <label htmlFor="st">阶段名称（每行一个）</label>
        <textarea
          id="st"
          rows={5}
          value={stages}
          onChange={(e) => setStages(e.target.value)}
        />
        <div style={{ marginTop: "0.5rem" }}>
          <button type="button" className="primary" onClick={savePipeline}>
            保存流水线
          </button>
        </div>
        <p style={{ fontSize: "0.9rem", color: "#666" }}>
          服务端当前阶段 ID：{job.current_stage_id ?? "无"}
        </p>
      </div>

      <Disclaimer />
    </div>
  );
}
