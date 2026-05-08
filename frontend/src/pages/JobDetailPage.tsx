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

function formatPublished(iso: string | null): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "—";
    return d.toLocaleDateString("zh-CN");
  } catch {
    return "—";
  }
}

type Resume = { id: number; title: string };

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const jid = Number(id);
  const [job, setJob] = useState<Job | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jd, setJd] = useState("");
  const [stages, setStages] = useState("笔试\n一面\n二面");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const j = await apiGet<Job>(`/api/jobs/${jid}`);
        setJob(j);
        setJd(j.jd_text);
        const rs = await apiGet<Resume[]>("/api/resumes/");
        setResumes(rs);
      } catch (e) {
        setErr(String(e));
      }
    })();
  }, [jid]);

  async function saveJd() {
    if (!job) return;
    setErr(null);
    try {
      const updated = await apiSend<Job>(`/api/jobs/${jid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jd_text: jd }),
      });
      setJob(updated);
    } catch (e) {
      setErr(String(e));
    }
  }

  async function linkResume(rid: number | "") {
    setErr(null);
    try {
      const updated = await apiSend<Job>(`/api/jobs/${jid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_id: rid === "" ? null : rid }),
      });
      setJob(updated);
    } catch (e) {
      setErr(String(e));
    }
  }

  async function savePipeline() {
    setErr(null);
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
    <div className="page">
      <p>
        <Link to="/jobs">← 列表</Link>
      </p>
      <h1>
        {job.company} — {job.title}
      </h1>
      <p style={{ color: "#666" }}>
        JD 抓取状态：
        {job.jd_fetch_status === "ok" ? "成功" : "失败"}（可在下方粘贴正文兜底）
      </p>
      {err ? <p className="err">{err}</p> : null}

      <div className="card job-detail-meta">
        <h2 className="resume-list-page__section-title">职位信息</h2>
        <dl className="job-meta-grid">
          <div>
            <dt>薪资</dt>
            <dd>{job.salary?.trim() ? job.salary : "—"}</dd>
          </div>
          <div>
            <dt>发布时间（解析）</dt>
            <dd>{formatPublished(job.published_at)}</dd>
          </div>
          <div className="job-meta-grid__full">
            <dt>JD 来源</dt>
            <dd>
              {job.jd_source_url ? (
                <a href={job.jd_source_url} target="_blank" rel="noreferrer">
                  {job.jd_source_url}
                </a>
              ) : (
                "—"
              )}
            </dd>
          </div>
        </dl>
      </div>

      <div className="card">
        <label>关联简历</label>
        <select
          value={job.resume_id ?? ""}
          onChange={(e) =>
            linkResume(e.target.value ? Number(e.target.value) : "")
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

      <div className="card">
        <label htmlFor="jd">JD 正文（可粘贴兜底）</label>
        <textarea
          id="jd"
          rows={12}
          value={jd}
          onChange={(e) => setJd(e.target.value)}
        />
        <div style={{ marginTop: "0.5rem" }}>
          <button type="button" className="primary" onClick={saveJd}>
            保存 JD
          </button>
        </div>
      </div>

      <div className="card">
        <label htmlFor="st">面试阶段（每行一个）</label>
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
          当前阶段 ID：{job.current_stage_id ?? "无"}
        </p>
      </div>

      <Disclaimer />
    </div>
  );
}
