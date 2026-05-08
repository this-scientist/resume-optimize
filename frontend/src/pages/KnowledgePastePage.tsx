import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";
import type { InterviewSourceListItem } from "../types/interviewSource";

export function KnowledgePastePage() {
  const navigate = useNavigate();
  const [note, setNote] = useState("");
  const [preview, setPreview] = useState<InterviewSourceListItem | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function saveDraft() {
    setErr(null);
    try {
      const data = await apiSend<InterviewSourceListItem>("/api/interview-sources/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note_text: note }),
      });
      setPreview(data);
    } catch (e) {
      setErr(String(e));
    }
  }

  async function confirm() {
    if (!preview) return;
    setErr(null);
    try {
      const res = await apiSend<{ index_status: string }>(
        `/api/interview-sources/${preview.id}/confirm`,
        { method: "POST" },
      );
      setPreview({ ...preview, index_status: res.index_status });
      navigate(`/knowledge/${preview.id}`, { replace: true });
    } catch (e) {
      setErr(String(e));
    }
  }

  return (
    <div className="page knowledge-subpage">
      <nav className="knowledge-subpage__nav">
        <Link to="/knowledge">← 返回列表</Link>
      </nav>
      <h1>粘贴笔记</h1>
      <p className="knowledge-subpage__lede">粘贴 Markdown 或纯文本，保存预览后可入库检索。</p>

      <div className="card">
        <label htmlFor="k-note">笔记内容</label>
        <textarea
          id="k-note"
          rows={10}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="支持 Markdown…"
        />
        <div style={{ marginTop: "0.75rem" }}>
          <button type="button" className="primary" onClick={() => void saveDraft()}>
            保存并预览
          </button>
        </div>
      </div>

      {err ? <p className="err">{err}</p> : null}

      {preview ? (
        <div className="card">
          <h2>预览 #{preview.id}</h2>
          <p>
            抓取：{preview.fetch_status} · 索引：{preview.index_status}
          </p>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              maxHeight: "280px",
              overflow: "auto",
              background: "#faf7f2",
              padding: "0.75rem",
              borderRadius: "8px",
            }}
          >
            {preview.body_preview}
          </pre>
          <button type="button" className="primary" onClick={() => void confirm()}>
            确认并入向量库
          </button>
        </div>
      ) : null}

      <Disclaimer />
    </div>
  );
}
