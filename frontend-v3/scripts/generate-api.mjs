import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const frontendDirectory = path.resolve(scriptDirectory, '..')
const repositoryDirectory = path.resolve(frontendDirectory, '..')
const schemaPath = path.join(frontendDirectory, 'src', 'api', 'generated', 'openapi-v3.json')
const typesPath = path.join(frontendDirectory, 'src', 'api', 'generated', 'schema.d.ts')

const repositoryPython = path.join(
  repositoryDirectory,
  '.venv',
  process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
)
const python = process.env.PYTHON || process.env.PYTHON_EXECUTABLE || repositoryPython

run(python, [path.join(repositoryDirectory, 'scripts', 'export_v3_openapi.py'), schemaPath], repositoryDirectory)
validateOpenApiSchema(schemaPath)
const npmCli = process.env.npm_execpath
if (!npmCli) {
  throw new Error('npm_execpath is required; run this generator through npm run generate:api')
}
run(
  process.execPath,
  [npmCli, 'run', 'generate', '--workspace', '@knowledge-island/openapi-codegen'],
  repositoryDirectory,
)
validateGeneratedTypes(typesPath)

function run(command, args, cwd) {
  const result = spawnSync(command, args, {
    cwd,
    encoding: 'utf8',
    stdio: 'inherit',
  })
  if (result.error) {
    throw result.error
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1)
  }
}

function validateOpenApiSchema(filename) {
  const schema = JSON.parse(readFileSync(filename, 'utf8'))
  if (schema.info?.version !== '3.0.0-alpha.2') {
    throw new Error(`Unexpected v3 OpenAPI version: ${schema.info?.version ?? 'missing'}`)
  }
  const discriminator = schema.components?.schemas?.AgentEvent?.discriminator?.propertyName
  if (discriminator !== 'event_type') {
    throw new Error(`AgentEvent discriminator must be event_type, received: ${discriminator ?? 'missing'}`)
  }
  if (!schema.paths?.['/runs/{run_id}/events']?.get) {
    throw new Error('v3 OpenAPI schema is missing the run event stream path')
  }
  const idempotentWrites = [
    ['/projects', 'post'],
    ['/projects/{project_id}/sources/scan', 'post'],
    ['/tasks', 'post'],
    ['/tasks/{task_id}/messages', 'post'],
    ['/tasks/{task_id}/runs', 'post'],
    ['/runs/{run_id}/pause', 'post'],
    ['/runs/{run_id}/resume', 'post'],
    ['/runs/{run_id}/cancel', 'post'],
    ['/runs/{run_id}/retry', 'post'],
    ['/approvals/{approval_id}/resolve', 'post'],
    ['/workflows', 'post'],
    ['/workflows/{workflow_id}/drafts', 'post'],
    ['/workflows/{workflow_id}/publish', 'post'],
    ['/workflows/{workflow_id}/archive', 'post'],
    ['/workflows/{workflow_id}/bindings', 'post'],
  ]
  for (const [route, method] of idempotentWrites) {
    const parameters = schema.paths?.[route]?.[method]?.parameters ?? []
    const hasRequiredIdempotencyKey = parameters.some(
      (parameter) =>
        parameter?.in === 'header' &&
        parameter?.name?.toLowerCase() === 'idempotency-key' &&
        parameter?.required === true,
    )
    if (!hasRequiredIdempotencyKey) {
      throw new Error(
        `v3 write operation is missing required Idempotency-Key: ${method.toUpperCase()} ${route}`,
      )
    }
  }
}

function validateGeneratedTypes(filename) {
  const generated = readFileSync(filename, 'utf8')
  for (const marker of ['export interface paths', 'AgentEvent:', '"/runs/{run_id}/events"']) {
    if (!generated.includes(marker)) {
      throw new Error(`Generated TypeScript schema is missing marker: ${marker}`)
    }
  }
}
