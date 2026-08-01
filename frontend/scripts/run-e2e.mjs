import { spawn } from "node:child_process";
import { existsSync, mkdtempSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, "..");
const projectRoot = path.resolve(frontendRoot, "..");
const backendPort = process.env.KI_E2E_BACKEND_PORT || "18765";
const frontendPort = process.env.KI_E2E_FRONTEND_PORT || "4173";
const apiBaseURL = process.env.KI_E2E_API_BASE_URL || `http://127.0.0.1:${backendPort}`;
const baseURL = process.env.KI_E2E_BASE_URL || `http://127.0.0.1:${frontendPort}`;
const e2eRuntimeDir = mkdtempSync(path.join(os.tmpdir(), "knowledge-island-e2e-"));

function pythonExecutable() {
  if (process.env.KI_E2E_PYTHON) {
    return process.env.KI_E2E_PYTHON;
  }
  const candidates = [
    path.join(projectRoot, ".venv", "Scripts", "python.exe"),
    path.join(projectRoot, ".venv", "bin", "python"),
  ];
  return candidates.find((candidate) => existsSync(candidate)) || "python";
}

function start(command, args, options = {}) {
  return spawn(command, args, {
    cwd: options.cwd || projectRoot,
    env: options.env || process.env,
    stdio: "inherit",
  });
}

async function waitForUrl(url, child, timeoutMs = 120_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`服务启动前已退出（code=${child.exitCode}）：${url}`);
    }
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
    } catch {
      // The process is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`等待服务启动超时：${url}`);
}

async function stop(child) {
  if (!child || child.exitCode !== null) {
    return;
  }
  const exited = new Promise((resolve) => child.once("exit", resolve));
  child.kill("SIGKILL");
  await Promise.race([
    exited,
    new Promise((resolve) => setTimeout(resolve, 5000)),
  ]);
}

const backend = start(
  pythonExecutable(),
  [path.join(projectRoot, "tests", "e2e", "e2e_server.py")],
  {
    env: {
      ...process.env,
      KI_E2E_PORT: backendPort,
      KI_DB_PATH: path.join(e2eRuntimeDir, "knowledge_island_e2e.db"),
      RAG_LLM_PROVIDER: "local",
    },
  },
);

const frontend = start(
  process.execPath,
  [
    path.join(projectRoot, "node_modules", "vite", "bin", "vite.js"),
    "preview",
    "--host",
    "127.0.0.1",
    "--port",
    frontendPort,
  ],
  { cwd: frontendRoot },
);

let exitCode = 1;
try {
  await Promise.all([
    waitForUrl(`${apiBaseURL}/api/health`, backend),
    waitForUrl(baseURL, frontend),
  ]);

  const playwright = start(
    process.execPath,
    [path.join(projectRoot, "node_modules", "@playwright", "test", "cli.js"), "test"],
    {
      cwd: frontendRoot,
      env: {
        ...process.env,
        KI_E2E_BACKEND_PORT: backendPort,
        KI_E2E_FRONTEND_PORT: frontendPort,
        KI_E2E_API_BASE_URL: apiBaseURL,
        KI_E2E_BASE_URL: baseURL,
      },
    },
  );
  exitCode = await new Promise((resolve) => playwright.once("exit", (code) => resolve(code ?? 1)));
} finally {
  await Promise.all([stop(frontend), stop(backend)]);
}

process.exitCode = exitCode;
