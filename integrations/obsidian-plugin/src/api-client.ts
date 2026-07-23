import { requestUrl } from "obsidian";

import { normalizeLoopbackBaseUrl } from "./logic";
import type {
  PairingCompleteResponse,
  PendingPublication,
  PublicationResultBatch,
  SyncEventResult,
  ObsidianSyncEvent,
} from "./types";

export class KnowledgeIslandApiClient {
  constructor(
    private readonly backendUrl: () => string,
    private readonly token: () => string,
  ) {}

  async completePairing(input: {
    code: string;
    vault_id: string;
    vault_name: string;
    output_root?: string;
  }): Promise<PairingCompleteResponse> {
    const response = await this.requestJson(
      "POST",
      "/api/obsidian/pairing/complete",
      input,
      false,
    );
    if (
      !isRecord(response)
      || !isRecord(response.connection)
      || typeof response.token !== "string"
      || response.token.length === 0
    ) {
      throw new Error("Knowledge Island returned an invalid pairing response.");
    }
    return response as unknown as PairingCompleteResponse;
  }

  async revokeConnection(connectionId: string): Promise<void> {
    await this.requestJson(
      "POST",
      "/api/obsidian/connections/revoke",
      { connection_id: connectionId },
      true,
    );
  }

  async sendEvents(events: ObsidianSyncEvent[]): Promise<SyncEventResult[]> {
    const response = await this.requestJson(
      "POST",
      "/api/obsidian/sync/events",
      { events },
      true,
    );
    if (!isRecord(response) || !Array.isArray(response.results)) {
      throw new Error("Knowledge Island returned an invalid sync response.");
    }
    return response.results as SyncEventResult[];
  }

  async pendingPublications(): Promise<PendingPublication[]> {
    const response = await this.requestJson(
      "GET",
      "/api/obsidian/publications/pending",
      undefined,
      true,
    );
    if (!isRecord(response) || !Array.isArray(response.publications)) {
      throw new Error("Knowledge Island returned an invalid pending publication response.");
    }
    return response.publications as PendingPublication[];
  }

  async reportPublicationResult(batch: PublicationResultBatch): Promise<void> {
    await this.requestJson(
      "POST",
      "/api/obsidian/publications/result",
      {
        publication_id: batch.publication_id,
        results: batch.results,
      },
      true,
    );
  }

  private async requestJson(
    method: "GET" | "POST",
    path: string,
    body: Record<string, unknown> | undefined,
    authenticated: boolean,
  ): Promise<unknown> {
    const baseUrl = normalizeLoopbackBaseUrl(this.backendUrl());
    const headers: Record<string, string> = {
      Accept: "application/json",
    };
    if (authenticated) {
      const token = this.token();
      if (!token) {
        throw new Error("Knowledge Island is not paired.");
      }
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await requestUrl({
      url: `${baseUrl}${path}`,
      method,
      headers,
      contentType: body === undefined ? undefined : "application/json",
      body: body === undefined ? undefined : JSON.stringify(body),
      throw: true,
    });
    return response.json;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
