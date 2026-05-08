import { useState } from "react";
import { apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";

type Preview = {
  id: number;
  body_preview: string;
  fetch_status: string;
  index_status: string;
};

export function KnowledgePage() {
  const [url, setUrl] = useState("");
  const [note, setNote] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function submit(kind: "url" | "note") {
    setErr(null);
    try {
      const body =
        kind === "url" ? { url } : { note_text: note };
      const data = await apiSend<Preview>("/api/interview-sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
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
    } catch (e) {
      setErr(String(e));
    }
  }

  return (
    <div className="page">
      <h1>面试知识</h1>
      <div className="card">
        <label htmlFor="url">从 URL 抓取</label>
        <input
          id="url"
          type="text"
          placeholder="https://..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <div style={{ marginTop: "0.75rem" }}>
          <button type="button" className="primary" onClick={() => submit("url")}>
            预览
          </button>
        </div>
      </div>
      <div className="card">
        <label htmlFor="note">或粘贴笔记（Markdown）</label>
        <textarea
          id="note"
          rows={8}
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        <div style={{ marginTop: "0.75rem" }}>
          <button type="button" className="primary" onClick={() => submit("note")}>
            保存笔记
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
          <button type="button" className="primary" onClick={confirm}>
            确认并入向量库
          </button>
        </div>
      ) : null}
      <Disclaimer />
    </div>
  );
}
