import "@uiw/react-md-editor/markdown-editor.css";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import MDEditor from "@uiw/react-md-editor";
import { apiGet, apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";

type Resume = {
  id: number;
  title: string;
  category: string;
  current_body_md: string;
};

type Job = { id: number; title: string; company: string };

export function ResumeEditPage() {
  const { id } = useParams<{ id: string }>();
  const rid = Number(id);
  const [row, setRow] = useState<Resume | null>(null);
  const [titleDraft, setTitleDraft] = useState("");
  const [md, setMd] = useState("");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobId, setJobId] = useState<number | "">("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const r = await apiGet<Resume>(`/api/resumes/${rid}`);
        setRow(r);
        setTitleDraft(r.title);
        setMd(r.current_body_md);
        const j = await apiGet<Job[]>("/api/jobs/");
        setJobs(j);
      } catch (e) {
        setErr(String(e));
      }
    })();
  }, [rid]);

  async function save() {
    setErr(null);
    try {
      const updated = await apiSend<Resume>(`/api/resumes/${rid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_body_md: md,
          title: titleDraft,
        }),
      });
      setRow(updated);
      setTitleDraft(updated.title);
      setMd(updated.current_body_md);
    } catch (e) {
      setErr(String(e));
    }
  }

  async function optimize() {
    if (!jobId) {
      setErr("请选择岗位");
      return;
    }
    setErr(null);
    try {
      await apiSend(`/api/resumes/${rid}/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, top_k: 8 }),
      });
      const r = await apiGet<Resume>(`/api/resumes/${rid}`);
      setRow(r);
      setTitleDraft(r.title);
      setMd(r.current_body_md);
    } catch (e) {
      setErr(String(e));
    }
  }

  if (!row) {
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
        <Link to="/resumes">← 列表</Link>
      </p>
      <h1>{titleDraft.trim() || `简历 #${rid}`}</h1>
      {err ? <p className="err">{err}</p> : null}

      <div className="card resume-edit-name">
        <label htmlFor="resume-title">简历名称</label>
        <input
          id="resume-title"
          type="text"
          autoComplete="off"
          placeholder="例如：互联网大厂通用版"
          value={titleDraft}
          onChange={(e) => setTitleDraft(e.target.value)}
          maxLength={255}
        />
        <p className="resume-list-page__hint">
          修改名称后点击页面底部「保存」会同步到列表与本地数据。
        </p>
      </div>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <label htmlFor="job">一键优化 · 选择岗位</label>
        <select
          id="job"
          value={jobId === "" ? "" : String(jobId)}
          onChange={(e) =>
            setJobId(e.target.value ? Number(e.target.value) : "")
          }
        >
          <option value="">请选择</option>
          {jobs.map((j) => (
            <option key={j.id} value={j.id}>
              {j.company} — {j.title}
            </option>
          ))}
        </select>
        <div style={{ marginTop: "0.5rem" }}>
          <button type="button" className="primary" onClick={optimize}>
            优化
          </button>
        </div>
      </div>
      <div data-color-mode="light">
        <MDEditor value={md} onChange={(v) => setMd(v ?? "")} height={420} />
      </div>
      <div style={{ marginTop: "0.75rem" }}>
        <button type="button" className="primary" onClick={save}>
          保存名称与正文
        </button>
      </div>
      <Disclaimer />
    </div>
  );
}
