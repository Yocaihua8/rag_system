import { spawn } from "node:child_process";
import { existsSync, mkdtempSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "../..");
const e2eRuntimeDir = mkdtempSync(path.join(os.tmpdir(), "knowledge-island-e2e-"));
const port = process.env.KI_E2E_PORT || "18765";

function pythonExecutable() {
  if (process.env.KI_E2E_PYTHON) {
    return process.env.KI_E2E_PYTHON;
  }

  const windowsVenv = path.join(projectRoot, ".venv", "Scripts", "python.exe");
  if (existsSync(windowsVenv)) {
    return windowsVenv;
  }

  const unixVenv = path.join(projectRoot, ".venv", "bin", "python");
  if (existsSync(unixVenv)) {
    return unixVenv;
  }

  return "python";
}

const child = spawn(pythonExecutable(), ["tests/e2e/e2e_server.py"], {
  cwd: projectRoot,
  env: {
    ...process.env,
    KI_E2E_PORT: port,
    KI_DB_PATH: path.join(e2eRuntimeDir, "knowledge_island_e2e.db"),
    RAG_LLM_PROVIDER: "local",
  },
  stdio: "inherit",
});

function shutdown(signal) {
  if (!child.killed) {
    child.kill(signal);
  }
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  }
  process.exit(code ?? 0);
});
