import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";

type Resume = {
  id: number;
  title: string;
  category: string;
};

export function ResumeListPage() {
  const [items, setItems] = useState<Resume[]>([]);
  const [title, setTitle] = useState("新简历");
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const data = await apiGet<Resume[]>("/api/resumes/");
      setItems(data);
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
      const r = await apiSend<Resume>("/api/resumes/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, category: "未分类", current_body_md: "" }),
      });
      await load();
      window.location.href = `/resumes/${r.id}`;
    } catch (e) {
      setErr(String(e));
    }
  }

  return (
    <div className="page">
      <h1>简历</h1>
      <div className="card">
        <label htmlFor="nt">新建标题</label>
        <input
          id="nt"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <div style={{ marginTop: "0.75rem" }}>
          <button type="button" className="primary" onClick={create}>
            创建并编辑
          </button>
        </div>
      </div>
      {err ? <p className="err">{err}</p> : null}
      <ul style={{ paddingLeft: "1.2rem" }}>
        {items.map((x) => (
          <li key={x.id}>
            <Link to={`/resumes/${x.id}`}>
              {x.title || `简历 #${x.id}`}
            </Link>
            <span style={{ color: "#888", marginLeft: "0.5rem" }}>
              {x.category}
            </span>
          </li>
        ))}
      </ul>
      <Disclaimer />
    </div>
  );
}
