import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { apiGet, apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";
import type { InterviewSourceDetail } from "../types/interviewSource";

function kindLabel(kind: string): string {
  if (kind === "url") return "URL 抓取";
  if (kind === "manual_note") return "粘贴笔记";
  return kind;
}

export function KnowledgeDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [row, setRow] = useState<InterviewSourceDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    if (!id || !/^\d+$/.test(id)) {
      setErr("无效的记录 ID");
      setLoading(false);
      return;
    }
    setErr(null);
    setLoading(true);
    try {
      const data = await apiGet<InterviewSourceDetail>(`/api/interview-sources/${id}`);
      setRow(data);
    } catch (e) {
      setErr(String(e).slice(0, 800) || "加载失败");
      setRow(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleDelete() {
    if (!id || !row) return;
    if (!window.confirm("确定删除此条记录？将同时移除向量库中对应片段。")) return;
    setDeleting(true);
    setErr(null);
    try {
      await apiSend(`/api/interview-sources/${id}`, { method: "DELETE" });
      navigate("/knowledge", { replace: true });
    } catch (e) {
      setErr(String(e).slice(0, 800));
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="page knowledge-detail-page">
      <nav className="knowledge-detail-page__nav">
        <Link to="/knowledge">← 返回列表</Link>
      </nav>

      {loading ? <p className="knowledge-detail-page__loading">加载中…</p> : null}

      {err && !loading ? <p className="err">{err}</p> : null}

      {!loading && row ? (
        <>
          <header className="knowledge-detail-page__header">
            <h1>{row.title?.trim() || row.url?.trim() || `记录 #${row.id}`}</h1>
            <p className="knowledge-detail-page__meta">
              {kindLabel(row.kind)}
              {" · "}
              抓取：{row.fetch_status} · 索引：{row.index_status}
              {" · "}
              {new Date(row.created_at).toLocaleString("zh-CN")}
            </p>
            {row.kind === "url" && row.url ? (
              <p className="knowledge-detail-page__url">
                <a href={row.url} target="_blank" rel="noreferrer">
                  {row.url}
                </a>
              </p>
            ) : null}
          </header>

          <section className="card knowledge-detail-page__body-card">
            <h2 className="knowledge-detail-page__body-heading">正文（Markdown / 纯文本）</h2>
            <pre className="knowledge-detail-page__body">{row.body_md || "（空）"}</pre>
          </section>

          <div className="knowledge-detail-page__actions">
            <button
              type="button"
              className="knowledge-detail-page__delete"
              onClick={() => void handleDelete()}
              disabled={deleting}
            >
              {deleting ? "删除中…" : "删除此记录"}
            </button>
          </div>
        </>
      ) : null}

      <Disclaimer />
    </div>
  );
}
