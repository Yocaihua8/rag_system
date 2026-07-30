import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  confirmObsidianPublication,
  listObsidianConnections,
  previewObsidianPublication,
  revokeObsidianConnection,
  startObsidianPairing,
} from "./obsidian.js";

function jsonResponse(data, init = {}) {
  return new Response(JSON.stringify(data), {
    status: init.status || 200,
    headers: { "Content-Type": "application/json" },
  });
}

function postBodyAt(index) {
  return JSON.parse(fetch.mock.calls[index][1].body);
}

describe("application-side Obsidian api helpers", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse({}));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("starts pairing, lists, and revokes project connections", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({ pairing: { code: "123456" } }))
      .mockResolvedValueOnce(jsonResponse({ connections: [{ id: "connection1" }] }))
      .mockResolvedValueOnce(jsonResponse({ connection: { id: "connection1", status: "revoked" } }));

    await expect(startObsidianPairing({
      projectId: " project / 1 ",
      outputRoot: " Knowledge Island/Demo/ ",
    })).resolves.toEqual({ pairing: { code: "123456" } });
    expect(postBodyAt(0)).toEqual({
      project_id: "project / 1",
      output_root: "Knowledge Island/Demo",
    });

    await expect(listObsidianConnections(" project / 1 ")).resolves.toEqual([{ id: "connection1" }]);
    expect(fetch.mock.calls[1][0]).toBe(
      "/api/obsidian/connections?project_id=project+%2F+1",
    );

    await revokeObsidianConnection({
      projectId: " project / 1 ",
      connectionId: " connection1 ",
    });
    expect(postBodyAt(2)).toEqual({
      project_id: "project / 1",
      connection_id: "connection1",
    });
  });

  it("previews selected artifacts or rollback sources and confirms a publication", async () => {
    fetch
      .mockResolvedValueOnce(jsonResponse({
        publication: { id: "publication1", status: "draft" },
        source_mode: "rollback",
        scope_notice: "仅表示当前项目",
      }))
      .mockResolvedValueOnce(jsonResponse({
        publication: { id: "publication1", status: "queued" },
        replayed: false,
      }));

    await expect(previewObsidianPublication({
      projectId: " p1 ",
      artifactTypes: ["project_understanding", "learning_plan"],
      assessmentSessionIds: ["session1"],
      sourcePublicationId: " old-publication ",
    })).resolves.toEqual({
      publication: { id: "publication1", status: "draft" },
      source_mode: "rollback",
      scope_notice: "仅表示当前项目",
    });
    expect(postBodyAt(0)).toEqual({
      project_id: "p1",
      artifact_types: ["project_understanding", "learning_plan"],
      assessment_session_ids: ["session1"],
      source_publication_id: "old-publication",
    });

    await expect(confirmObsidianPublication({
      projectId: "p1",
      publicationId: " publication1 ",
    })).resolves.toEqual({
      publication: { id: "publication1", status: "queued" },
      replayed: false,
    });
    expect(postBodyAt(1)).toEqual({
      project_id: "p1",
      publication_id: "publication1",
    });
  });

  it("validates application selections and exposes no plugin-token endpoints", async () => {
    await expect(startObsidianPairing({ projectId: " " })).rejects.toThrow(
      "请先创建或选择项目空间",
    );
    await expect(revokeObsidianConnection({
      projectId: "p1",
      connectionId: "",
    })).rejects.toThrow("请选择 Obsidian 连接");

    const module = await import("./obsidian.js");
    expect(Object.keys(module).sort()).toEqual([
      "confirmObsidianPublication",
      "listObsidianConnections",
      "previewObsidianPublication",
      "revokeObsidianConnection",
      "startObsidianPairing",
    ]);
  });
});
