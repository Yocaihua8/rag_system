import {
  createProject,
  deleteDocument,
  deleteSelectedProject,
  getDocument,
  importSelectedProject,
  listDocuments,
  refreshProjects,
  renameSelectedProject,
  selectProject,
} from "./projects.js";
import { ask, search, startAssessment, submitAssessmentAnswer } from "./qa.js";
import { state } from "./state.js";
import {
  renderAnswer,
  renderDocumentCount,
  renderDocumentPreview,
  renderDocuments,
  renderImportErrors,
  renderProjectRoot,
  renderAssessmentQuestion,
  renderAssessmentResult,
  renderSearchResults,
  renderSkippedDetails,
  setStatus,
} from "./ui.js";

const projectForm = document.querySelector("#project-form");
const projectSelect = document.querySelector("#project-select");
const projectRootEl = document.querySelector("#project-root");
const importButton = document.querySelector("#import-button");
const renameProjectButton = document.querySelector("#rename-project-button");
const deleteProjectButton = document.querySelector("#delete-project-button");
const askButton = document.querySelector("#ask-button");
const searchButton = document.querySelector("#search-button");
const answerEl = document.querySelector("#answer");
const sourcesEl = document.querySelector("#sources");
const documentsEl = document.querySelector("#documents");
const documentFilterInput = document.querySelector("#document-filter");
const documentCountEl = document.querySelector("#document-count");
const documentPreviewEl = document.querySelector("#document-preview");
const searchResultsEl = document.querySelector("#search-results");
const skippedDetailsEl = document.querySelector("#skipped-details");
const importErrorsEl = document.querySelector("#import-errors");
const startAssessmentButton = document.querySelector("#start-assessment-button");
const assessmentQuestionEl = document.querySelector("#assessment-question");
const assessmentAnswerInput = document.querySelector("#assessment-answer");
const assessmentAnswerButton = document.querySelector("#assessment-answer-button");
const assessmentResultEl = document.querySelector("#assessment-result");

projectSelect.addEventListener("change", async () => {
  selectProject(projectSelect.value);
  renderSelectedProjectRoot();
  await refreshDocuments();
});

projectForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    setStatus("正在创建项目空间...");
    await createProject(projectForm);
    await refreshProjects(projectSelect);
    projectSelect.value = state.selectedProjectId;
    renderSelectedProjectRoot();
    state.documents = [];
    renderFilteredDocuments();
    renderDocumentPreview(documentPreviewEl, null);
    renderSearchResults(searchResultsEl, [], previewDocument);
    renderSkippedDetails(skippedDetailsEl, []);
    renderImportErrors(importErrorsEl, []);
    setStatus("项目空间已创建，可点击导入。");
  } catch (error) {
    setStatus(error.message);
  }
});

importButton.addEventListener("click", async () => {
  try {
    setStatus("正在导入文本资料...");
    const data = await importSelectedProject();
    state.documents = data.documents;
    renderFilteredDocuments();
    renderDocumentPreview(documentPreviewEl, null);
    renderSearchResults(searchResultsEl, [], previewDocument);
    renderSkippedDetails(skippedDetailsEl, data.result.skipped_details);
    renderImportErrors(importErrorsEl, data.result.errors);
    setStatus(
      `导入完成：新增 ${data.result.created}，更新 ${data.result.updated}，未变更 ${data.result.unchanged}，删除 ${data.result.deleted}，跳过 ${data.result.skipped}。`,
    );
  } catch (error) {
    setStatus(error.message);
  }
});

renameProjectButton.addEventListener("click", async () => {
  const currentProject = state.projects.find((project) => project.id === state.selectedProjectId);
  const nextName = prompt("输入新的项目名称", currentProject?.name || "");
  if (nextName === null) {
    return;
  }
  try {
    setStatus("正在修改项目名称...");
    await renameSelectedProject(nextName);
    await refreshProjects(projectSelect);
    projectSelect.value = state.selectedProjectId;
    renderSelectedProjectRoot();
    setStatus("项目名称已更新。");
  } catch (error) {
    setStatus(error.message);
  }
});

deleteProjectButton.addEventListener("click", async () => {
  if (!confirm("确认删除当前项目空间？此操作会删除该项目空间下的文档记录。")) {
    return;
  }
  try {
    setStatus("正在删除项目空间...");
    await deleteSelectedProject();
    await refreshProjects(projectSelect);
    renderSelectedProjectRoot();
    await refreshDocuments();
    setStatus("项目空间已删除。");
  } catch (error) {
    setStatus(error.message);
  }
});

documentFilterInput.addEventListener("input", () => {
  state.documentFilter = documentFilterInput.value.trim();
  renderFilteredDocuments();
});

searchButton.addEventListener("click", async () => {
  const query = document.querySelector("#search-query").value.trim();
  if (!query) {
    setStatus("请输入检索关键词。");
    return;
  }
  try {
    setStatus("正在检索文件片段...");
    const data = await search(query);
    renderSearchResults(searchResultsEl, data.hits, previewDocument);
    setStatus(`找到 ${data.hits.length} 条结果。`);
  } catch (error) {
    setStatus(error.message);
  }
});

askButton.addEventListener("click", async () => {
  const question = document.querySelector("#question").value.trim();
  if (!question) {
    setStatus("请输入问题。");
    return;
  }
  try {
    setStatus("正在检索资料...");
    renderAnswer(answerEl, sourcesEl, await ask(question));
    setStatus("已返回答案。");
  } catch (error) {
    setStatus(error.message);
  }
});

startAssessmentButton.addEventListener("click", async () => {
  try {
    setStatus("正在生成评估题...");
    const data = await startAssessment();
    state.assessmentSession = data.session;
    state.assessmentQuestion = data.session.questions[0] || null;
    assessmentAnswerInput.value = "";
    renderAssessmentQuestion(assessmentQuestionEl, state.assessmentQuestion);
    renderAssessmentResult(assessmentResultEl, null);
    setStatus("评估题已生成。");
  } catch (error) {
    setStatus(error.message);
  }
});

assessmentAnswerButton.addEventListener("click", async () => {
  const answer = assessmentAnswerInput.value.trim();
  if (!answer) {
    setStatus("请输入评估回答。");
    return;
  }
  try {
    setStatus("正在评估回答...");
    const data = await submitAssessmentAnswer(answer);
    renderAssessmentResult(assessmentResultEl, data.result);
    setStatus("评估反馈已生成。");
  } catch (error) {
    setStatus(error.message);
  }
});

async function refreshDocuments() {
  const data = await listDocuments();
  state.documents = data.documents;
  renderFilteredDocuments();
  renderDocumentPreview(documentPreviewEl, null);
  renderSearchResults(searchResultsEl, [], previewDocument);
  renderSkippedDetails(skippedDetailsEl, []);
  renderImportErrors(importErrorsEl, []);
  state.assessmentSession = null;
  state.assessmentQuestion = null;
  renderAssessmentQuestion(assessmentQuestionEl, null);
  renderAssessmentResult(assessmentResultEl, null);
}

function renderFilteredDocuments() {
  const filterText = state.documentFilter.toLowerCase();
  const documents = filterText
    ? state.documents.filter((document) => document.relative_path.toLowerCase().includes(filterText))
    : state.documents;
  const emptyMessage = state.documents.length === 0 ? "暂无导入文件" : "没有匹配文件";
  renderDocuments(documentsEl, documents, previewDocument, removeDocument, emptyMessage);
  renderDocumentCount(documentCountEl, documents.length, state.documents.length);
}

function renderSelectedProjectRoot() {
  const project = state.projects.find((entry) => entry.id === state.selectedProjectId);
  renderProjectRoot(projectRootEl, project);
}

async function removeDocument(documentId) {
  if (!confirm("确认从当前项目空间移除这个文档记录？源文件不会被删除。")) {
    return;
  }
  try {
    setStatus("正在移除文档记录...");
    const data = await deleteDocument(documentId);
    state.documents = data.documents;
    renderFilteredDocuments();
    renderDocumentPreview(documentPreviewEl, null);
    renderSearchResults(searchResultsEl, [], previewDocument);
    setStatus("文档记录已移除。");
  } catch (error) {
    setStatus(error.message);
  }
}

async function previewDocument(documentId) {
  try {
    setStatus("正在读取文件预览...");
    const data = await getDocument(documentId);
    renderDocumentPreview(documentPreviewEl, data.document);
    setStatus("已显示文件预览。");
  } catch (error) {
    setStatus(error.message);
  }
}

refreshProjects(projectSelect)
  .then(() => {
    renderSelectedProjectRoot();
    return refreshDocuments();
  })
  .catch((error) => setStatus(error.message));
