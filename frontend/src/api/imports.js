import { apiPost } from "./client.js";

export async function importPlainTextNote({ projectId, title, content }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const cleanTitle = title.trim();
  const cleanContent = content.trim();
  if (!cleanTitle) {
    throw new Error("请输入笔记标题");
  }
  if (!cleanContent) {
    throw new Error("请输入笔记正文");
  }
  return apiPost("/api/import/note", {
    project_id: projectId,
    title: cleanTitle,
    content: cleanContent,
  });
}

export async function importUrlExcerpt({ projectId, url, title, content }) {
  if (!projectId) {
    throw new Error("请先创建或选择项目空间");
  }
  const cleanUrl = url.trim();
  const cleanTitle = title.trim();
  const cleanContent = content.trim();
  if (!cleanUrl) {
    throw new Error("请输入 URL");
  }
  if (!cleanTitle) {
    throw new Error("请输入网页标题");
  }
  if (!cleanContent) {
    throw new Error("请输入网页正文或摘要");
  }
  return apiPost("/api/import/url", {
    project_id: projectId,
    url: cleanUrl,
    title: cleanTitle,
    content: cleanContent,
  });
}
