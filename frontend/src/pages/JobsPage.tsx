import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";
import { apiGet, apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";

type JobRow = {
  id: number;
  company: string;
  title: string;
  salary: string;
  published_at: string | null;
  jd_fetch_status: string;
  jd_source_url: string | null;
};

function formatPublished(iso: string | null): string {
  if (!iso) return "—";
  const prefix = /^(\d{4}-\d{2}-\d{2})/.exec(iso);
  if (prefix) {
    const [y, mo, day] = prefix[1].split("-").map(Number);
    return new Date(y, mo - 1, day).toLocaleDateString("zh-CN");
  }
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "—";
    return d.toLocaleDateString("zh-CN");
  } catch {
    return "—";
  }
}

export function JobsPage() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [items, setItems] = useState<JobRow[]>([]);
  const [query, setQuery] = useState("");
  const [listLoading, setListLoading] = useState(true);
  const [listErr, setListErr] = useState<string | null>(null);
  const [jdUrl, setJdUrl] = useState("");
  const [modalBusy, setModalBusy] = useState(false);
  const [modalErr, setModalErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setListErr(null);
    setListLoading(true);
    try {
      const data = await apiGet<JobRow[]>("/api/jobs/");
      setItems(data);
    } catch (e) {
      setListErr(
        String(e).slice(0, 600) ||
          "加载失败，请确认后端已启动（默认 http://127.0.0.1:8000）。",
      );
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((row) => {
      const hay = [
        row.company,
        row.title,
        row.salary,
        String(row.id),
        row.jd_source_url ?? "",
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [items, query]);

  const openModal = () => {
    setModalErr(null);
    setJdUrl("");
    dialogRef.current?.showModal();
  };

  const closeModal = () => {
    if (modalBusy) return;
    dialogRef.current?.close();
    setModalErr(null);
  };

  async function handleModalSubmit(e: FormEvent) {
    e.preventDefault();
    const u = jdUrl.trim();
    if (!u.startsWith("http://") && !u.startsWith("https://")) {
      setModalErr("请填写以 http:// 或 https:// 开头的 JD 职位页链接。");
      return;
    }
    setModalErr(null);
    setModalBusy(true);
    try {
      await apiSend("/api/jobs/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jd_source_url: u }),
      });
      dialogRef.current?.close();
      setJdUrl("");
      await load();
    } catch (err) {
      setModalErr(String(err).slice(0, 800));
    } finally {
      setModalBusy(false);
    }
  }

  const showEmpty = !listLoading && !listErr && items.length === 0;
  const showNoMatch =
    !listLoading && !listErr && items.length > 0 && filtered.length === 0;

  return (
    <div className="page jobs-page">
      <header className="jobs-page__intro">
        <h1>岗位</h1>
        <p className="jobs-page__lede">
          仅通过 JD 页面链接抓取职位与公司等信息；详情页可粘贴正文或配置面试阶段。
        </p>
      </header>

      <div className="jobs-toolbar card">
        <div className="jobs-toolbar__search">
          <label htmlFor="job-search" className="visually-hidden">
            搜索岗位
          </label>
          <input
            id="job-search"
            type="search"
            placeholder="搜索公司、职位、薪资…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoComplete="off"
          />
        </div>
        <div className="jobs-toolbar__actions">
          <button type="button" className="btn-secondary" onClick={() => void load()}>
            刷新
          </button>
          <button type="button" className="primary" onClick={openModal}>
            新建岗位
          </button>
        </div>
      </div>

      <div className="jobs-page__feedback" aria-live="polite">
        {listErr ? (
          <div className="error-banner" role="alert">
            <div className="error-banner__text">{listErr}</div>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => void load()}
            >
              重试
            </button>
          </div>
        ) : null}
      </div>

      <section className="jobs-table-section" aria-labelledby="jobs-table-title">
        <h2 id="jobs-table-title" className="visually-hidden">
          岗位列表
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
            <p className="empty-state__title">暂无岗位</p>
            <p className="empty-state__body">
              点击右上角「新建岗位」，粘贴招聘详情页的完整 URL，系统将尝试抓取 JD 正文并解析公司、职位、薪资与发布时间。
            </p>
          </div>
        ) : null}

        {showNoMatch ? (
          <p className="jobs-page__hint">没有匹配的岗位，请调整搜索词。</p>
        ) : null}

        {!listLoading && !listErr && filtered.length > 0 ? (
          <div className="jobs-table-wrap">
            <table className="jobs-table">
              <thead>
                <tr>
                  <th scope="col">公司</th>
                  <th scope="col">职位</th>
                  <th scope="col">薪资</th>
                  <th scope="col">发布时间</th>
                  <th scope="col">抓取</th>
                  <th scope="col">操作</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr key={row.id}>
                    <td>{row.company || "—"}</td>
                    <td>{row.title || "—"}</td>
                    <td>{row.salary || "—"}</td>
                    <td>{formatPublished(row.published_at)}</td>
                    <td>
                      <span
                        className={
                          row.jd_fetch_status === "ok"
                            ? "badge badge--ok"
                            : "badge badge--bad"
                        }
                      >
                        {row.jd_fetch_status === "ok" ? "成功" : "失败"}
                      </span>
                    </td>
                    <td>
                      <Link className="jobs-table__link" to={`/jobs/${row.id}`}>
                        详情
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <dialog
        ref={dialogRef}
        className="job-modal"
        aria-labelledby="job-modal-title"
        onClose={() => setModalErr(null)}
      >
        <form className="job-modal__form" onSubmit={handleModalSubmit}>
          <h2 id="job-modal-title" className="job-modal__title">
            新建岗位
          </h2>
          <p className="job-modal__desc">
            请粘贴第三方招聘网站上的<strong>职位详情页</strong>链接（需公网可访问）。系统将抓取页面并尝试识别公司、职位、薪资与发布日期。
          </p>
          <label htmlFor="jd-url-input">JD 页面 URL（必填）</label>
          <input
            id="jd-url-input"
            type="url"
            inputMode="url"
            placeholder="https://"
            value={jdUrl}
            onChange={(e) => setJdUrl(e.target.value)}
            disabled={modalBusy}
            autoFocus
            required
          />
          {modalErr ? (
            <p className="err job-modal__err" role="alert">
              {modalErr}
            </p>
          ) : null}
          <div className="job-modal__actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={closeModal}
              disabled={modalBusy}
            >
              取消
            </button>
            <button
              type="submit"
              className="primary"
              disabled={modalBusy}
              aria-busy={modalBusy}
            >
              {modalBusy ? "抓取中…" : "创建"}
            </button>
          </div>
        </form>
      </dialog>

      <Disclaimer />
    </div>
  );
}
