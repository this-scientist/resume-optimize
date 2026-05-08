const API = import.meta.env.VITE_API_BASE ?? "";

export async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<T>;
}

export async function apiSend<T>(
  path: string,
  init: RequestInit,
): Promise<T> {
  const r = await fetch(`${API}${path}`, init);
  if (!r.ok) throw new Error(await r.text());
  if (r.status === 204) return undefined as T;
  return r.json() as Promise<T>;
}
