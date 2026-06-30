import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiGet, apiPost } from "./client.js";

function jsonResponse(data, init = {}) {
  return new Response(JSON.stringify(data), {
    status: init.status || 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("apiGet returns parsed JSON from the requested path", async () => {
    fetch.mockResolvedValueOnce(jsonResponse({ ok: true }));

    await expect(apiGet("/api/projects")).resolves.toEqual({ ok: true });

    expect(fetch).toHaveBeenCalledWith("/api/projects");
  });

  it("apiPost sends JSON payload and forwards AbortController signal", async () => {
    const signal = new AbortController().signal;
    fetch.mockResolvedValueOnce(jsonResponse({ saved: true }));

    await expect(apiPost("/api/projects", { name: "项目" }, { signal })).resolves.toEqual({ saved: true });

    expect(fetch).toHaveBeenCalledWith("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "项目" }),
      signal,
    });
  });

  it("uses backend JSON error messages when HTTP responses fail", async () => {
    fetch.mockResolvedValueOnce(jsonResponse({ error: "项目不存在" }, { status: 404 }));

    await expect(apiGet("/api/project")).rejects.toThrow("项目不存在");
  });

  it("normalizes non-JSON successful responses as response format errors", async () => {
    fetch.mockResolvedValueOnce(new Response("plain text", { status: 200 }));

    await expect(apiGet("/api/plain")).rejects.toThrow("服务返回格式异常。请刷新页面后重试。");
  });

  it("normalizes non-JSON failed responses with HTTP status", async () => {
    fetch.mockResolvedValueOnce(new Response("not found", { status: 503 }));

    await expect(apiGet("/api/unavailable")).rejects.toThrow("服务返回异常（HTTP 503）。请确认应用已启动后刷新页面。");
  });

  it("normalizes fetch TypeError as local service unavailable", async () => {
    fetch.mockRejectedValueOnce(new TypeError("fetch failed"));

    await expect(apiGet("/api/health")).rejects.toThrow("本地服务暂时不可用。请确认应用已启动后刷新页面。");
  });
});
