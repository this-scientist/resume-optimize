import { useCallback, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";
import type { InterviewSourceListItem } from "../types/interviewSource";

type DiscoveredLink = { url: string; label: string | null };

export function KnowledgeImportPage() {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [preview, setPreview] = useState<InterviewSourceListItem | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [discoverLoading, setDiscoverLoading] = useState(false);
  const [discovered, setDiscovered] = useState<DiscoveredLink[] | null>(null);
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(new Set());
  const [batchBusy, setBatchBusy] = useState(false);
  const [batchCreated, setBatchCreated] = useState<InterviewSourceListItem[] | null>(null);

  const toggleUrl = useCallback((u: string) => {
    setSelectedUrls((prev) => {
      const n = new Set(prev);
      if (n.has(u)) n.delete(u);
      else n.add(u);
      return n;
    });
  }, []);

  const selectAll = useCallback(() => {
    if (!discovered) return;
    setSelectedUrls(new Set(discovered.map((l) => l.url)));
  }, [discovered]);

  const selectNone = useCallback(() => {
    setSelectedUrls(new Set());
  }, []);

  async function submitPreview() {
    setErr(null);
    setDiscovered(null);
    setBatchCreated(null);
    try {
      const data = await apiSend<InterviewSourceListItem>("/api/interview-sources/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      setPreview(data);
    } catch (e) {
      setErr(String(e));
    }
  }

  async function discoverLinks() {
    setErr(null);
    setDiscoverLoading(true);
    setPreview(null);
    setBatchCreated(null);
    try {
      const data = await apiSend<{ base_url: string; links: DiscoveredLink[] }>(
        "/api/interview-sources/discover-links",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: url.trim(), max_links: 80 }),
        },
      );
      setDiscovered(data.links);
      setSelectedUrls(new Set(data.links.map((l) => l.url)));
    } catch (e) {
      setErr(String(e));
      setDiscovered(null);
    } finally {
      setDiscoverLoading(false);
    }
  }

  async function batchCreate() {
    if (!discovered || selectedUrls.size === 0) return;
    setErr(null);
    setBatchBusy(true);
    try {
      const urls = Array.from(selectedUrls);
      const rows = await apiSend<InterviewSourceListItem[]>("/api/interview-sources/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls }),
      });
      setBatchCreated(rows);
      setPreview(null);
    } catch (e) {
      setErr(String(e));
    } finally {
      setBatchBusy(false);
    }
  }

  async function batchConfirm() {
    if (!batchCreated?.length) return;
    const okIds = batchCreated.filter((r) => r.fetch_status === "ok").map((r) => r.id);
    if (okIds.length === 0) {
      setErr("没有抓取成功的页面可入库（正文过短或抓取失败）。请从列表删除失败项后单独处理。");
      return;
    }
    setErr(null);
    setBatchBusy(true);
    try {
      await apiSend<Array<{ id: number; index_status: string }>>(
        "/api/interview-sources/batch-confirm",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source_ids: okIds }),
        },
      );
      navigate("/knowledge", { replace: true });
    } catch (e) {
      setErr(String(e));
    } finally {
      setBatchBusy(false);
    }
  }

  async function confirmSingle() {
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

  const failedBatch =
    batchCreated?.filter((r) => r.fetch_status === "failed").length ?? 0;

  return (
    <div className="page knowledge-subpage">
      <nav className="knowledge-subpage__nav">
        <Link to="/knowledge">← 返回列表</Link>
      </nav>
      <h1>从 URL 导入</h1>
      <p className="knowledge-subpage__lede">
        可预览单页，或使用「发现站内链接」抓取导航/目录中的同站页面并批量入库。
      </p>

      <div className="card">
        <label htmlFor="k-url">页面地址</label>
        <input
          id="k-url"
          type="text"
          placeholder="https://..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <div className="knowledge-import__actions">
          <button type="button" className="primary" onClick={() => void submitPreview()}>
            仅预览当前页
          </button>
          <button
            type="button"
            className="primary"
            disabled={discoverLoading || !url.trim()}
            onClick={() => void discoverLinks()}
          >
            {discoverLoading ? "分析链接中…" : "发现站内链接"}
          </button>
        </div>
      </div>

      {err ? <p className="err">{err}</p> : null}

      {discovered && discovered.length > 0 ? (
        <div className="card knowledge-import__discover">
          <h2>发现的链接（同站 · 已选 {selectedUrls.size} / {discovered.length}）</h2>
          <p className="knowledge-import__hint">
            默认全选；可取消不需要的条目，再批量抓取。外链、mailto、常见静态资源已过滤。
            批量抓取会按上一页正文字数估算「阅读时间」，再以一半时长作为请求间隔，降低并发冲击。
          </p>
          <div className="knowledge-import__toolbar">
            <button type="button" className="btn-secondary" onClick={selectAll}>
              全选
            </button>
            <button type="button" className="btn-secondary" onClick={selectNone}>
              全不选
            </button>
            <button
              type="button"
              className="primary"
              disabled={batchBusy || selectedUrls.size === 0}
              onClick={() => void batchCreate()}
            >
              {batchBusy ? "抓取中…" : "批量抓取并创建记录"}
            </button>
          </div>
          <div className="knowledge-import__table-wrap">
            <table className="knowledge-import__table">
              <thead>
                <tr>
                  <th scope="col">选</th>
                  <th scope="col">标题 / 锚文本</th>
                  <th scope="col">URL</th>
                </tr>
              </thead>
              <tbody>
                {discovered.map((l) => (
                  <tr key={l.url}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedUrls.has(l.url)}
                        onChange={() => toggleUrl(l.url)}
                        aria-label={`选择 ${l.url}`}
                      />
                    </td>
                    <td>{l.label || "—"}</td>
                    <td className="knowledge-import__url-cell">{l.url}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {discovered && discovered.length === 0 ? (
        <p className="knowledge-import__empty">未发现同站链接，请改用「仅预览当前页」或检查 URL。</p>
      ) : null}

      {batchCreated && batchCreated.length > 0 ? (
        <div className="card">
          <h2>已创建 {batchCreated.length} 条记录</h2>
          {failedBatch > 0 ? (
            <>
              <p className="err">
                其中 {failedBatch} 条抓取失败（正文过短或反爬），可在列表中删除后重试。
              </p>
              <p className="knowledge-import__hint">
                「全部写入向量库」仅会处理抓取成功的条目。
              </p>
            </>
          ) : (
            <p>抓取成功，可一键写入向量库。</p>
          )}
          <ul className="knowledge-import__batch-summary">
            {batchCreated.map((r) => (
              <li key={r.id}>
                #{r.id} · {r.fetch_status === "ok" ? "抓取 OK" : "抓取失败"} ·{" "}
                {(r.title || r.url || "").slice(0, 80)}
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="primary"
            disabled={batchBusy}
            onClick={() => void batchConfirm()}
          >
            {batchBusy ? "写入中…" : "全部写入向量库"}
          </button>
        </div>
      ) : null}

      {preview && !batchCreated ? (
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
          <button type="button" className="primary" onClick={() => void confirmSingle()}>
            确认并入向量库
          </button>
        </div>
      ) : null}

      <Disclaimer />
    </div>
  );
}
