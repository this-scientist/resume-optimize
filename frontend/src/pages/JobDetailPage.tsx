import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiGet, apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";

type Job = {
  id: number;
  company: string;
  title: string;
  jd_text: string;
  jd_fetch_status: string;
  resume_id: number | null;
  current_stage_id: number | null;
};

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
        JD 抓取状态：{job.jd_fetch_status}
      </p>
      {err ? <p className="err">{err}</p> : null}

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
