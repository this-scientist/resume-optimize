import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";

type Job = {
  id: number;
  company: string;
  title: string;
  jd_fetch_status: string;
};

export function JobsPage() {
  const [items, setItems] = useState<Job[]>([]);
  const [company, setCompany] = useState("");
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      setItems(await apiGet<Job[]>("/api/jobs/"));
    } catch (e) {
      setErr(String(e));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function create() {
    setErr(null);
    try {
      const body: Record<string, unknown> = { company, title };
      if (url.trim()) body.jd_source_url = url.trim();
      const j = await apiSend<Job>("/api/jobs/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await load();
      window.location.href = `/jobs/${j.id}`;
    } catch (e) {
      setErr(String(e));
    }
  }

  return (
    <div className="page">
      <h1>岗位</h1>
      <div className="card">
        <label>公司</label>
        <input value={company} onChange={(e) => setCompany(e.target.value)} />
        <label style={{ marginTop: "0.5rem" }}>职位</label>
        <input value={title} onChange={(e) => setTitle(e.target.value)} />
        <label style={{ marginTop: "0.5rem" }}>JD 页面 URL（可选）</label>
        <input
          placeholder="https://..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <div style={{ marginTop: "0.75rem" }}>
          <button type="button" className="primary" onClick={create}>
            创建
          </button>
        </div>
      </div>
      {err ? <p className="err">{err}</p> : null}
      <ul style={{ paddingLeft: "1.2rem" }}>
        {items.map((x) => (
          <li key={x.id}>
            <Link to={`/jobs/${x.id}`}>
              {x.company} — {x.title}
            </Link>
            <span style={{ color: "#888", marginLeft: "0.5rem" }}>
              {x.jd_fetch_status}
            </span>
          </li>
        ))}
      </ul>
      <Disclaimer />
    </div>
  );
}
