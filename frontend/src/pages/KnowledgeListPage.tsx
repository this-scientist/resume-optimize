import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";
import type { InterviewSourceListItem } from "../types/interviewSource";

function kindLabel(kind: string): string {
  if (kind === "url") return "URL";
  if (kind === "manual_note") return "粘贴笔记";
  return kind;
}

function indexLabel(s: string): string {
  if (s === "indexed") return "已入库";
  if (s === "failed") return "索引失败";
  if (s === "pending") return "待确认";
  return s;
}

function rowTitle(x: InterviewSourceListItem): string {
  const t = x.title?.trim();
  if (t) return t;
  const u = x.url?.trim();
  if (u) return u.length > 56 ? `${u.slice(0, 54)}…` : u;
  return `笔记 #${x.id}`;
}

export function KnowledgeListPage() {
  const [items, setItems] = useState<InterviewSourceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await apiGet<InterviewSourceListItem[]>("/api/interview-sources/");
      setItems(data);
    } catch (e) {
      setErr(
        String(e).slice(0, 800) ||
          "列表加载失败，请确认后端已启动（默认连接 http://127.0.0.1:8000）。",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const empty = !loading && !err && items.length === 0;

  return (
    <div className="page knowledge-list-page">
      <header className="knowledge-list-page__intro">
        <h1>面试知识</h1>
        <p className="knowledge-list-page__lede">
          管理已导入的面试笔记与网页摘录；优化简历时会从向量库检索相关内容。
        </p>
      </header>

      <section className="card knowledge-list-page__toolbar" aria-label="导入入口">
        <div className="knowledge-list-page__toolbar-inner">
          <Link className="primary knowledge-list-page__toolbar-btn" to="/knowledge/import">
            从 URL 导入
          </Link>
          <Link className="primary knowledge-list-page__toolbar-btn" to="/knowledge/paste">
            粘贴笔记
          </Link>
        </div>
      </section>

      <div className="knowledge-list-page__feedback" aria-live="polite">
        {err ? (
          <div className="error-banner" role="alert">
            <div className="error-banner__text">{err}</div>
            <button type="button" className="btn-secondary" onClick={() => void load()}>
              重试
            </button>
          </div>
        ) : null}
      </div>

      <section className="knowledge-list-page__list-section" aria-labelledby="knowledge-list-heading">
        <h2 id="knowledge-list-heading" className="knowledge-list-page__section-title">
          全部记录
        </h2>

        {loading ? (
          <div className="resume-skeleton" aria-hidden="true">
            <div className="resume-skeleton__row" />
            <div className="resume-skeleton__row" />
            <div className="resume-skeleton__row resume-skeleton__row--short" />
          </div>
        ) : null}

        {empty ? (
          <div className="empty-state" role="status">
            <p className="empty-state__title">还没有记录</p>
            <p className="empty-state__body">
              使用上方「从 URL 导入」或「粘贴笔记」添加内容，确认后会写入本地向量库供简历优化检索。
            </p>
          </div>
        ) : null}

        {!loading && !err && items.length > 0 ? (
          <ul className="resume-list knowledge-list" role="list">
            {items.map((x) => (
              <li key={x.id} className="resume-list__item">
                <Link className="resume-list__link" to={`/knowledge/${x.id}`}>
                  <span className="resume-list__title">{rowTitle(x)}</span>
                  <span className="resume-list__meta">
                    {kindLabel(x.kind)} · {indexLabel(x.index_status)} ·{" "}
                    {new Date(x.created_at).toLocaleString("zh-CN", {
                      dateStyle: "short",
                      timeStyle: "short",
                    })}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <Disclaimer />
    </div>
  );
}
