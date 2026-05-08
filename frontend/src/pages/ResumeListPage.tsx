import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiGet, apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";

type Resume = {
  id: number;
  title: string;
  category: string;
};

export function ResumeListPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<Resume[]>([]);
  const [title, setTitle] = useState("新简历");
  const [listLoading, setListLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [listErr, setListErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setListErr(null);
    setListLoading(true);
    try {
      const data = await apiGet<Resume[]>("/api/resumes/");
      setItems(data);
    } catch (e) {
      setListErr(
        String(e).slice(0, 800) ||
          "列表加载失败，请确认后端已启动（默认 http://127.0.0.1:8000）。",
      );
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCreate() {
    if (creating) return;
    setListErr(null);
    setCreating(true);
    try {
      const r = await apiSend<Resume>("/api/resumes/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, category: "未分类", current_body_md: "" }),
      });
      navigate(`/resumes/${r.id}`);
    } catch (e) {
      setListErr(
        `创建失败：${String(e)}`.slice(0, 800),
      );
    } finally {
      setCreating(false);
    }
  }

  const showEmpty =
    !listLoading && !listErr && items.length === 0;

  return (
    <div className="page resume-list-page">
      <header className="resume-list-page__intro">
        <h1>简历</h1>
        <p className="resume-list-page__lede">
          在此管理 Markdown 简历；编辑页可关联岗位并一键优化。
        </p>
      </header>

      <section className="card resume-list-page__create" aria-labelledby="create-heading">
        <h2 id="create-heading" className="resume-list-page__section-title">
          新建简历
        </h2>
        <label htmlFor="resume-new-title">标题</label>
        <input
          id="resume-new-title"
          type="text"
          autoComplete="off"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          disabled={creating}
          aria-describedby="resume-new-hint"
        />
        <p id="resume-new-hint" className="resume-list-page__hint">
          创建后将直接进入编辑器；可随时返回此列表。
        </p>
        <div className="resume-list-page__create-actions">
          <button
            type="button"
            className="primary"
            onClick={() => void handleCreate()}
            disabled={creating || listLoading}
            aria-busy={creating}
          >
            {creating ? "创建中…" : "创建并编辑"}
          </button>
        </div>
      </section>

      <div className="resume-list-page__feedback" aria-live="polite">
        {listErr ? (
          <div className="error-banner" role="alert">
            <div className="error-banner__text">{listErr}</div>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => void load()}
            >
              重试加载列表
            </button>
          </div>
        ) : null}
      </div>

      <section className="resume-list-page__list-section" aria-labelledby="list-heading">
        <h2 id="list-heading" className="resume-list-page__section-title">
          全部简历
        </h2>

        {listLoading ? (
          <div className="resume-skeleton" aria-hidden="true">
            <div className="resume-skeleton__row" />
            <div className="resume-skeleton__row" />
            <div className="resume-skeleton__row resume-skeleton__row--short" />
          </div>
        ) : null}

        {showEmpty ? (
          <div className="empty-state" role="status">
            <p className="empty-state__title">还没有简历</p>
            <p className="empty-state__body">
              在上方填写标题，点击「创建并编辑」即可开始；之后你会在这里看到所有简历条目。
            </p>
          </div>
        ) : null}

        {!listLoading && !listErr && items.length > 0 ? (
          <ul className="resume-list" role="list">
            {items.map((x) => (
              <li key={x.id} className="resume-list__item">
                <Link
                  className="resume-list__link"
                  to={`/resumes/${x.id}`}
                >
                  <span className="resume-list__title">
                    {x.title?.trim() || `简历 #${x.id}`}
                  </span>
                  <span className="resume-list__meta">{x.category}</span>
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
