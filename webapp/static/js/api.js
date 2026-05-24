const SERVICE_UNAVAILABLE_MESSAGE = "本地服务暂时不可用。请确认应用已启动后刷新页面。";

export async function apiGet(path) {
  try {
    const response = await fetch(path);
    return readJson(response);
  } catch (error) {
    throw normalizeFetchError(error);
  }
}

export async function apiPost(path, payload) {
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return readJson(response);
  } catch (error) {
    throw normalizeFetchError(error);
  }
}

async function readJson(response) {
  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    if (!response.ok) {
      throw new Error(`服务返回异常（HTTP ${response.status}）。请确认应用已启动后刷新页面。`);
    }
    throw new Error("服务返回格式异常。请刷新页面后重试。");
  }
  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

function normalizeFetchError(error) {
  if (error instanceof TypeError) {
    return new Error(SERVICE_UNAVAILABLE_MESSAGE);
  }
  return error;
}
