import { apiGet } from "./client.js";

const SERVICE_UNAVAILABLE_MESSAGE = "本地服务暂时不可用。请确认应用已启动后刷新页面。";

export async function getOllamaStatus() {
  return apiGet("/api/ollama/status");
}

export async function pullOllamaModel({ model, handlers = {}, signal } = {}) {
  const cleanModel = String(model || "").trim();
  if (!cleanModel) {
    throw new Error("请选择要下载的模型");
  }

  let response = null;
  try {
    response = await fetch("/api/ollama/pull", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: cleanModel }),
      signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw error;
    }
    throw new Error(SERVICE_UNAVAILABLE_MESSAGE);
  }

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  if (!response.body) {
    throw new Error("当前环境不支持模型下载进度流");
  }
  return readOllamaPullStream(response, handlers);
}

async function readOllamaPullStream(response, handlers) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let doneData = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const result = consumeSseEvents(buffer, handlers);
    buffer = result.buffer;
    doneData = result.doneData || doneData;
  }

  buffer += decoder.decode();
  if (buffer.trim()) {
    const result = consumeSseEvents(`${buffer}\n\n`, handlers);
    doneData = result.doneData || doneData;
  }
  return doneData || { status: "done" };
}

function consumeSseEvents(buffer, handlers) {
  const chunks = buffer.split("\n\n");
  const remainder = chunks.pop() || "";
  let doneData = null;

  for (const chunk of chunks) {
    if (!chunk.trim()) {
      continue;
    }
    const { event, data } = parseSseEvent(chunk);
    if (event === "progress") {
      handlers.onProgress?.(data);
    } else if (event === "done") {
      handlers.onDone?.(data);
      doneData = data;
    } else if (event === "error") {
      handlers.onError?.(data);
      throw new Error(data.error || "模型下载失败");
    }
  }

  return { buffer: remainder, doneData };
}

function parseSseEvent(chunk) {
  let event = "message";
  const dataLines = [];
  for (const line of chunk.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }
  return {
    event,
    data: parseJsonPayload(dataLines.join("\n")),
  };
}

function parseJsonPayload(payload) {
  try {
    return JSON.parse(payload || "{}");
  } catch (error) {
    throw new Error("模型下载进度格式异常。请重试。");
  }
}

async function readErrorMessage(response) {
  try {
    const data = await response.json();
    return data.error || `HTTP ${response.status}`;
  } catch (error) {
    return `HTTP ${response.status}`;
  }
}
