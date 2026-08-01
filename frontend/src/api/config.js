const DEFAULT_API_BASE_URL = "http://127.0.0.1:8765";

function normalizeApiBaseUrl(value) {
  const normalized = String(value || DEFAULT_API_BASE_URL).trim().replace(/\/+$/, "");
  const parsed = new URL(normalized);
  if (
    !["http:", "https:"].includes(parsed.protocol)
    || parsed.username
    || parsed.password
    || parsed.pathname !== "/"
    || parsed.search
    || parsed.hash
  ) {
    throw new Error("VITE_API_BASE_URL 必须是仅包含协议、主机和端口的 HTTP(S) 地址");
  }
  return normalized;
}

export const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);

export function apiUrl(path) {
  const normalizedPath = String(path || "").startsWith("/") ? String(path) : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}
