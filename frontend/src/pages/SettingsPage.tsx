import { useEffect, useState } from "react";
import { apiGet, apiSend } from "../api/client";
import { Disclaimer } from "../components/Disclaimer";

type Settings = {
  chat_base_url: string;
  chat_api_key: string;
  chat_model: string;
  embedding_base_url: string;
  embedding_api_key: string;
  embedding_model: string;
};

export function SettingsPage() {
  const [form, setForm] = useState<Settings | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const s = await apiGet<Settings>("/api/settings/");
        setForm({
          ...s,
          chat_api_key: "",
          embedding_api_key: "",
        });
      } catch (e) {
        setErr(String(e));
      }
    })();
  }, []);

  async function save() {
    if (!form) return;
    setErr(null);
    try {
      const saved = await apiSend<Settings>("/api/settings/", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      setForm({
        ...saved,
        chat_api_key: "",
        embedding_api_key: "",
      });
    } catch (e) {
      setErr(String(e));
    }
  }

  function field<K extends keyof Settings>(key: K, value: Settings[K]) {
    setForm((f) => (f ? { ...f, [key]: value } : f));
  }

  if (!form) {
    return (
      <div className="page">
        {err ? <p className="err">{err}</p> : <p>加载中…</p>}
        <Disclaimer />
      </div>
    );
  }

  return (
    <div className="page">
      <h1>模型设置</h1>
      <p style={{ color: "#666" }}>
        API Key 保存后再次打开需重新填写完整密钥（列表仅显示掩码）。
      </p>
      {err ? <p className="err">{err}</p> : null}
      <div className="card">
        <h3>Chat</h3>
        <label>Base URL</label>
        <input
          value={form.chat_base_url}
          onChange={(e) => field("chat_base_url", e.target.value)}
        />
        <label style={{ marginTop: "0.5rem" }}>API Key</label>
        <input
          type="password"
          autoComplete="off"
          placeholder="留空则不在此修改"
          value={form.chat_api_key}
          onChange={(e) => field("chat_api_key", e.target.value)}
        />
        <label style={{ marginTop: "0.5rem" }}>Model</label>
        <input
          value={form.chat_model}
          onChange={(e) => field("chat_model", e.target.value)}
        />
      </div>
      <div className="card">
        <h3>Embedding</h3>
        <label>Base URL</label>
        <input
          value={form.embedding_base_url}
          onChange={(e) => field("embedding_base_url", e.target.value)}
        />
        <label style={{ marginTop: "0.5rem" }}>API Key</label>
        <input
          type="password"
          autoComplete="off"
          placeholder="留空则不在此修改"
          value={form.embedding_api_key}
          onChange={(e) => field("embedding_api_key", e.target.value)}
        />
        <label style={{ marginTop: "0.5rem" }}>Model</label>
        <input
          value={form.embedding_model}
          onChange={(e) => field("embedding_model", e.target.value)}
        />
      </div>
      <button type="button" className="primary" onClick={save}>
        保存
      </button>
      <Disclaimer />
    </div>
  );
}
