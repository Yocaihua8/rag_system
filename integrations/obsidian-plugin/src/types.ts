export type SyncEventType = "upsert" | "rename" | "delete";

export interface ObsidianSyncEvent {
  event_id: string;
  type: SyncEventType;
  path: string;
  old_path?: string;
  content?: string;
  content_hash?: string;
  frontmatter: Record<string, unknown>;
  tags: string[];
  resolved_links: Record<string, number>;
  unresolved_links: Record<string, number>;
  occurred_at: string;
}

export interface ConnectionView {
  id: string;
  project_id: string;
  vault_id: string;
  output_root: string;
  status: string;
}

export interface PairingCompleteResponse {
  connection: ConnectionView;
  token: string;
  token_type: "Bearer";
}

export interface SyncEventResult {
  event_id: string;
  status: "applied" | "ignored" | "failed";
  document_id?: string;
  action?: string;
  error?: string;
}

export interface PublicationArtifact {
  revision_id: string;
  artifact_type: string;
  stable_id: string;
  target_path: string;
  content: string;
  content_hash: string;
  expected_vault_hash?: string | null;
  frontmatter?: Record<string, unknown>;
}

export interface PendingPublication {
  id: string;
  project_id: string;
  revision: number;
  status: "queued";
  artifacts: PublicationArtifact[];
}

export type PublicationResultStatus = "applied" | "conflict" | "failed";

export interface PublicationArtifactResult {
  revision_id: string;
  status: PublicationResultStatus;
  actual_hash?: string;
  error_code?: string;
  message?: string;
}

export interface PublicationResultBatch {
  publication_id: string;
  results: PublicationArtifactResult[];
}

export interface PluginState {
  backend_url: string;
  vault_id: string;
  connection_id: string;
  project_id: string;
  token: string;
  output_root: string;
  next_event_sequence: number;
  event_queue: ObsidianSyncEvent[];
  publication_result_queue: PublicationResultBatch[];
  poll_interval_seconds: number;
}

export const DEFAULT_PLUGIN_STATE: PluginState = {
  backend_url: "http://127.0.0.1:8765",
  vault_id: "",
  connection_id: "",
  project_id: "",
  token: "",
  output_root: "",
  next_event_sequence: 1,
  event_queue: [],
  publication_result_queue: [],
  poll_interval_seconds: 15,
};

export interface ManagedMetadata {
  knowledge_island_managed: true;
  knowledge_island_id: string;
  knowledge_island_project_id: string;
  knowledge_island_artifact_type: string;
  knowledge_island_revision: number;
}
