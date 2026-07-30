import type {
  ManagedMetadata,
  PendingPublication,
  PublicationArtifact,
} from "./types";

export class BridgeConflict extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "BridgeConflict";
    this.code = code;
  }
}

export type PathNormalizer = (path: string) => string;

export function normalizeLoopbackBaseUrl(rawUrl: string): string {
  let url: URL;
  try {
    url = new URL(String(rawUrl ?? "").trim());
  } catch {
    throw new Error("Knowledge Island service URL is invalid.");
  }
  if (!["http:", "https:"].includes(url.protocol)) {
    throw new Error("Knowledge Island service URL must use HTTP or HTTPS.");
  }
  if (!["127.0.0.1", "localhost", "::1", "[::1]"].includes(url.hostname.toLowerCase())) {
    throw new Error("Knowledge Island service must use a loopback address.");
  }
  if (url.username || url.password || (url.pathname !== "/" && url.pathname !== "")) {
    throw new Error("Knowledge Island service URL cannot include credentials or a path.");
  }
  url.search = "";
  url.hash = "";
  return url.toString().replace(/\/$/, "");
}

export function safeVaultPath(rawPath: string, normalize: PathNormalizer): string {
  const source = String(rawPath ?? "").trim().replaceAll("\\", "/");
  if (!source) {
    throw new BridgeConflict("invalid_path", "Vault path is required.");
  }
  if (
    source.startsWith("/")
    || source.startsWith("//")
    || /^[a-zA-Z]:/.test(source)
    || source.includes("\0")
  ) {
    throw new BridgeConflict("invalid_path", "Vault path must be relative.");
  }
  if (source.split("/").some((part) => part === "..")) {
    throw new BridgeConflict("path_outside_output_root", "Parent traversal is not allowed.");
  }

  const normalized = normalize(source);
  if (
    !normalized
    || normalized === "."
    || normalized.startsWith("../")
    || normalized.includes("/../")
  ) {
    throw new BridgeConflict("invalid_path", "Vault path is invalid.");
  }
  return normalized;
}

export function isPathInsideRoot(path: string, outputRoot: string): boolean {
  return path === outputRoot || path.startsWith(`${outputRoot}/`);
}

export function validatePublicationPath(
  rawPath: string,
  rawOutputRoot: string,
  normalize: PathNormalizer,
): string {
  const path = safeVaultPath(rawPath, normalize);
  const outputRoot = safeVaultPath(rawOutputRoot, normalize);
  if (!isPathInsideRoot(path, outputRoot)) {
    throw new BridgeConflict(
      "path_outside_output_root",
      "Publication target is outside the configured output root.",
    );
  }
  if (!path.toLocaleLowerCase().endsWith(".md")) {
    throw new BridgeConflict("target_not_markdown", "Publication target must be Markdown.");
  }
  return path;
}

export function classifyRename(
  oldPath: string,
  newPath: string,
  outputRoot: string,
): "ignore" | "delete" | "upsert" | "rename" {
  const oldExcluded = isPathInsideRoot(oldPath, outputRoot);
  const newExcluded = isPathInsideRoot(newPath, outputRoot);
  if (oldExcluded && newExcluded) {
    return "ignore";
  }
  if (!oldExcluded && newExcluded) {
    return "delete";
  }
  if (oldExcluded && !newExcluded) {
    return "upsert";
  }
  return "rename";
}

export function stableEventId(connectionId: string, sequence: number): string {
  if (!connectionId || !Number.isSafeInteger(sequence) || sequence < 1) {
    throw new Error("connectionId and a positive integer sequence are required");
  }
  return `${connectionId}:${sequence.toString(36).padStart(10, "0")}`;
}

export function expectedManagedMetadata(
  publication: PendingPublication,
  artifact: PublicationArtifact,
): ManagedMetadata {
  return {
    knowledge_island_managed: true,
    knowledge_island_id: artifact.stable_id,
    knowledge_island_project_id: publication.project_id,
    knowledge_island_artifact_type: artifact.artifact_type,
    knowledge_island_revision: publication.revision,
  };
}

export function managedMetadataFromContent(content: string): Record<string, unknown> {
  const match = content.match(/^(?:\uFEFF)?---[ \t]*\r?\n([\s\S]*?)\r?\n---[ \t]*(?:\r?\n|$)/);
  if (!match) {
    return {};
  }

  const metadata: Record<string, unknown> = {};
  for (const line of match[1].split(/\r?\n/)) {
    const field = line.match(/^([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$/);
    if (!field) {
      continue;
    }
    metadata[field[1]] = parseYamlScalar(field[2]);
  }
  return metadata;
}

export function assertManagedMetadata(
  actual: Record<string, unknown>,
  expected: ManagedMetadata,
): void {
  if (!isTrue(actual.knowledge_island_managed)) {
    throw new BridgeConflict(
      "unmanaged_target",
      "Existing target is not managed by Knowledge Island.",
    );
  }
  if (String(actual.knowledge_island_id ?? "") !== expected.knowledge_island_id) {
    throw new BridgeConflict("stable_id_mismatch", "Managed stable ID does not match.");
  }
  if (
    String(actual.knowledge_island_project_id ?? "")
    !== expected.knowledge_island_project_id
  ) {
    throw new BridgeConflict("project_id_mismatch", "Managed project ID does not match.");
  }
  if (
    String(actual.knowledge_island_artifact_type ?? "")
    !== expected.knowledge_island_artifact_type
  ) {
    throw new BridgeConflict("artifact_type_mismatch", "Managed artifact type does not match.");
  }
}

export function sha256Hex(input: string): string {
  const bytes = new TextEncoder().encode(input);
  const bitLength = bytes.length * 8;
  const withOne = bytes.length + 1;
  const totalLength = Math.ceil((withOne + 8) / 64) * 64;
  const padded = new Uint8Array(totalLength);
  padded.set(bytes);
  padded[bytes.length] = 0x80;

  const view = new DataView(padded.buffer);
  const high = Math.floor(bitLength / 0x1_0000_0000);
  const low = bitLength >>> 0;
  view.setUint32(totalLength - 8, high, false);
  view.setUint32(totalLength - 4, low, false);

  const state = new Uint32Array([
    0x6a09e667,
    0xbb67ae85,
    0x3c6ef372,
    0xa54ff53a,
    0x510e527f,
    0x9b05688c,
    0x1f83d9ab,
    0x5be0cd19,
  ]);
  const schedule = new Uint32Array(64);

  for (let offset = 0; offset < totalLength; offset += 64) {
    for (let index = 0; index < 16; index += 1) {
      schedule[index] = view.getUint32(offset + index * 4, false);
    }
    for (let index = 16; index < 64; index += 1) {
      const x = schedule[index - 15];
      const y = schedule[index - 2];
      const sigma0 = rotateRight(x, 7) ^ rotateRight(x, 18) ^ (x >>> 3);
      const sigma1 = rotateRight(y, 17) ^ rotateRight(y, 19) ^ (y >>> 10);
      schedule[index] = (
        schedule[index - 16]
        + sigma0
        + schedule[index - 7]
        + sigma1
      ) >>> 0;
    }

    let a = state[0];
    let b = state[1];
    let c = state[2];
    let d = state[3];
    let e = state[4];
    let f = state[5];
    let g = state[6];
    let h = state[7];

    for (let index = 0; index < 64; index += 1) {
      const sigma1 = rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
      const choose = (e & f) ^ (~e & g);
      const temp1 = (h + sigma1 + choose + SHA256_CONSTANTS[index] + schedule[index]) >>> 0;
      const sigma0 = rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
      const majority = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (sigma0 + majority) >>> 0;

      h = g;
      g = f;
      f = e;
      e = (d + temp1) >>> 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) >>> 0;
    }

    state[0] = (state[0] + a) >>> 0;
    state[1] = (state[1] + b) >>> 0;
    state[2] = (state[2] + c) >>> 0;
    state[3] = (state[3] + d) >>> 0;
    state[4] = (state[4] + e) >>> 0;
    state[5] = (state[5] + f) >>> 0;
    state[6] = (state[6] + g) >>> 0;
    state[7] = (state[7] + h) >>> 0;
  }

  return Array.from(state, (word) => word.toString(16).padStart(8, "0")).join("");
}

function parseYamlScalar(raw: string): unknown {
  const value = raw.trim();
  if (
    (value.startsWith("\"") && value.endsWith("\""))
    || (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  if (/^-?\d+$/.test(value)) {
    return Number(value);
  }
  return value;
}

function isTrue(value: unknown): boolean {
  return value === true || String(value).toLocaleLowerCase() === "true";
}

function rotateRight(value: number, amount: number): number {
  return (value >>> amount) | (value << (32 - amount));
}

const SHA256_CONSTANTS = new Uint32Array([
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
  0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
  0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
  0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
  0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
  0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
  0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
  0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
  0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]);
