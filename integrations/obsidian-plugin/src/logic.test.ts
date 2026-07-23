import { describe, expect, it } from "vitest";

import {
  assertManagedMetadata,
  BridgeConflict,
  classifyRename,
  expectedManagedMetadata,
  isPathInsideRoot,
  managedMetadataFromContent,
  normalizeLoopbackBaseUrl,
  safeVaultPath,
  sha256Hex,
  stableEventId,
  validatePublicationPath,
} from "./logic";
import type { PendingPublication, PublicationArtifact } from "./types";

const normalize = (path: string): string => path
  .split("/")
  .filter((part) => part !== "" && part !== ".")
  .join("/");

describe("Vault path protection", () => {
  it("normalizes a relative path and rejects traversal or absolute paths", () => {
    expect(safeVaultPath("Notes//topic.md", normalize)).toBe("Notes/topic.md");
    expect(() => safeVaultPath("../secret.md", normalize)).toThrowError(
      expect.objectContaining({ code: "path_outside_output_root" }),
    );
    expect(() => safeVaultPath("C:\\secret.md", normalize)).toThrowError(
      expect.objectContaining({ code: "invalid_path" }),
    );
    expect(() => safeVaultPath("/secret.md", normalize)).toThrowError(
      expect.objectContaining({ code: "invalid_path" }),
    );
  });

  it("uses an exact output-root boundary", () => {
    expect(isPathInsideRoot("Knowledge Island/Project", "Knowledge Island/Project")).toBe(true);
    expect(isPathInsideRoot("Knowledge Island/Project/计划.md", "Knowledge Island/Project")).toBe(true);
    expect(isPathInsideRoot("Knowledge Island/Project-old.md", "Knowledge Island/Project")).toBe(false);
  });

  it("only allows Markdown targets under the configured output root", () => {
    expect(
      validatePublicationPath(
        "Knowledge Island/Project/学习计划.md",
        "Knowledge Island/Project",
        normalize,
      ),
    ).toBe("Knowledge Island/Project/学习计划.md");
    expect(() => validatePublicationPath(
      "Knowledge Island/Other/学习计划.md",
      "Knowledge Island/Project",
      normalize,
    )).toThrowError(expect.objectContaining({ code: "path_outside_output_root" }));
    expect(() => validatePublicationPath(
      "Knowledge Island/Project/data.json",
      "Knowledge Island/Project",
      normalize,
    )).toThrowError(expect.objectContaining({ code: "target_not_markdown" }));
  });
});

describe("local service boundary", () => {
  it("accepts loopback HTTP endpoints without retaining query data", () => {
    expect(normalizeLoopbackBaseUrl("http://127.0.0.1:8765/")).toBe(
      "http://127.0.0.1:8765",
    );
    expect(normalizeLoopbackBaseUrl("https://localhost:9443/?probe=1")).toBe(
      "https://localhost:9443",
    );
  });

  it.each([
    "https://example.com",
    "file:///tmp/service",
    "http://user:password@127.0.0.1:8765",
    "http://127.0.0.1:8765/api",
  ])("rejects non-loopback or over-scoped service URL %s", (url) => {
    expect(() => normalizeLoopbackBaseUrl(url)).toThrow();
  });
});

describe("Vault event identity and rename routing", () => {
  it("keeps the connection-scoped event id stable for a persisted sequence", () => {
    expect(stableEventId("connection-1", 42)).toBe("connection-1:0000000016");
    expect(stableEventId("connection-1", 42)).toBe(stableEventId("connection-1", 42));
    expect(stableEventId("connection-2", 42)).not.toBe(stableEventId("connection-1", 42));
  });

  it("does not feed managed output back into source ingestion", () => {
    const root = "Knowledge Island/Project";
    expect(classifyRename(`${root}/a.md`, `${root}/b.md`, root)).toBe("ignore");
    expect(classifyRename("Notes/a.md", `${root}/a.md`, root)).toBe("delete");
    expect(classifyRename(`${root}/a.md`, "Notes/a.md", root)).toBe("upsert");
    expect(classifyRename("Notes/a.md", "Notes/b.md", root)).toBe("rename");
  });
});

describe("managed publication validation", () => {
  const artifact: PublicationArtifact = {
    revision_id: "revision-1",
    artifact_type: "learning_plan",
    stable_id: "plan-main",
    target_path: "Knowledge Island/Project/学习计划.md",
    content: "",
    content_hash: "",
    expected_vault_hash: "",
  };
  const publication: PendingPublication = {
    id: "publication-1",
    project_id: "project-1",
    revision: 3,
    status: "queued",
    artifacts: [artifact],
  };
  const expected = expectedManagedMetadata(publication, artifact);

  it("parses and accepts all required managed markers", () => {
    const content = [
      "---",
      "knowledge_island_managed: true",
      "knowledge_island_id: plan-main",
      "knowledge_island_project_id: project-1",
      "knowledge_island_artifact_type: learning_plan",
      "knowledge_island_revision: 3",
      "---",
      "# 学习计划",
    ].join("\n");
    const metadata = managedMetadataFromContent(content);
    expect(metadata.knowledge_island_revision).toBe(3);
    expect(() => assertManagedMetadata(metadata, expected)).not.toThrow();
  });

  it.each([
    ["unmanaged_target", { knowledge_island_managed: false }],
    ["stable_id_mismatch", { knowledge_island_id: "other" }],
    ["project_id_mismatch", { knowledge_island_project_id: "other" }],
    ["artifact_type_mismatch", { knowledge_island_artifact_type: "overview" }],
  ])("blocks %s instead of overwriting", (code, override) => {
    const actual = { ...expected, ...override };
    expect(() => assertManagedMetadata(actual, expected)).toThrowError(
      expect.objectContaining({ code }),
    );
  });

  it("uses a real SHA-256 content hash", () => {
    expect(sha256Hex("")).toBe(
      "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    );
    expect(sha256Hex("知识岛")).toBe(
      "a1a9d99d60a59bc5f8ad28224327df923d000437f4475fdb208d8cbc419aa4bd",
    );
  });
});

describe("BridgeConflict", () => {
  it("retains a machine-readable conflict code", () => {
    const error = new BridgeConflict("vault_hash_conflict", "changed");
    expect(error.code).toBe("vault_hash_conflict");
    expect(error.message).toBe("changed");
  });
});
