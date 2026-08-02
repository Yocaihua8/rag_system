import { spawn } from 'node:child_process'
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  writeFileSync,
} from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const frontendDirectory = path.resolve(scriptDirectory, '..')
const repositoryDirectory = path.resolve(frontendDirectory, '..')
const backendPort = process.env.KI_V3_E2E_BACKEND_PORT || '18766'
const frontendPort = process.env.KI_V3_E2E_FRONTEND_PORT || '4174'
const apiBaseUrl = `http://127.0.0.1:${backendPort}/api/v3`
const frontendBaseUrl = `http://127.0.0.1:${frontendPort}`
const e2eRoot = mkdtempSync(path.join(os.tmpdir(), 'knowledge-island-v3-e2e-'))
const projectRoot = path.join(e2eRoot, 'sample-project')

mkdirSync(path.join(projectRoot, 'src'), { recursive: true })
writeFileSync(
  path.join(projectRoot, 'README.md'),
  '# E2E Project\n\nA local fixture used by the real v3 executor.\n',
  'utf8',
)
writeFileSync(path.join(projectRoot, 'src', 'main.py'), 'def main():\n    return "ok"\n', 'utf8')

function pythonExecutable() {
  if (process.env.KI_V3_E2E_PYTHON) return process.env.KI_V3_E2E_PYTHON
  const candidates = [
    path.join(repositoryDirectory, '.venv', 'Scripts', 'python.exe'),
    path.join(repositoryDirectory, '.venv', 'bin', 'python'),
  ]
  return candidates.find((candidate) => existsSync(candidate)) || 'python'
}

function start(command, args, options = {}) {
  return spawn(command, args, {
    cwd: options.cwd || repositoryDirectory,
    env: options.env || process.env,
    stdio: 'inherit',
  })
}

async function runToCompletion(command, args, options = {}) {
  const child = start(command, args, options)
  const exitCode = await new Promise((resolve) =>
    child.once('exit', (code) => resolve(code ?? 1)),
  )
  if (exitCode !== 0) {
    throw new Error(`${path.basename(command)} exited with code ${exitCode}`)
  }
}

async function waitForUrl(url, child, timeoutMs = 120_000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`Service exited before it became ready (code=${child.exitCode}): ${url}`)
    }
    try {
      const response = await fetch(url)
      if (response.ok) return
    } catch {
      // The service is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250))
  }
  throw new Error(`Timed out while waiting for ${url}`)
}

async function stop(child, shutdownUrl) {
  if (!child || child.exitCode !== null) return
  if (shutdownUrl) {
    try {
      await fetch(shutdownUrl, { method: 'POST' })
    } catch {
      // Fall back to terminating the exact child started by this runner.
    }
  }
  const exited = new Promise((resolve) => child.once('exit', resolve))
  const timeout = new Promise((resolve) => setTimeout(resolve, 5_000, 'timeout'))
  if ((await Promise.race([exited, timeout])) === 'timeout' && child.exitCode === null) {
    child.kill('SIGKILL')
  }
}

const viteCli = path.join(frontendDirectory, 'node_modules', 'vite', 'bin', 'vite.js')
const playwrightCli = path.join(
  repositoryDirectory,
  'node_modules',
  '@playwright',
  'test',
  'cli.js',
)
const commonEnvironment = {
  ...process.env,
  VITE_API_BASE_URL: apiBaseUrl,
  KI_CORS_ORIGINS: `${frontendBaseUrl},http://localhost:${frontendPort}`,
  KI_V3_E2E_API_BASE_URL: apiBaseUrl,
  KI_V3_E2E_BASE_URL: frontendBaseUrl,
  KI_V3_E2E_PROJECT_ROOT: projectRoot,
}

let backend
let frontend
let exitCode = 1
try {
  await runToCompletion(process.execPath, [viteCli, 'build', '--mode', 'e2e'], {
    cwd: frontendDirectory,
    env: commonEnvironment,
  })

  backend = start(
    pythonExecutable(),
    [path.join(repositoryDirectory, 'tests', 'e2e', 'v3_e2e_server.py')],
    {
      env: {
        ...commonEnvironment,
        KI_V3_E2E_PORT: backendPort,
        KI_V3_E2E_V2_DB_PATH: path.join(e2eRoot, 'v2.db'),
        KI_V3_E2E_DB_PATH: path.join(e2eRoot, 'v3.db'),
      },
    },
  )
  frontend = start(
    process.execPath,
    [viteCli, 'preview', '--host', '127.0.0.1', '--port', frontendPort, '--strictPort'],
    { cwd: frontendDirectory, env: commonEnvironment },
  )

  await Promise.all([
    waitForUrl(`${apiBaseUrl}/health`, backend),
    waitForUrl(frontendBaseUrl, frontend),
  ])

  const playwright = start(process.execPath, [playwrightCli, 'test'], {
    cwd: frontendDirectory,
    env: commonEnvironment,
  })
  exitCode = await new Promise((resolve) =>
    playwright.once('exit', (code) => resolve(code ?? 1)),
  )
} finally {
  await Promise.all([
    stop(frontend),
    stop(backend, `http://127.0.0.1:${backendPort}/__e2e__/shutdown`),
  ])
  rmSync(e2eRoot, { recursive: true, force: true })
}

process.exitCode = exitCode
