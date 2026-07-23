import {
  getAllTags,
  normalizePath,
  Plugin,
  TFile,
  type CachedMetadata,
  type TAbstractFile,
} from "obsidian";

import { KnowledgeIslandApiClient } from "./api-client";
import {
  classifyRename,
  isPathInsideRoot,
  normalizeLoopbackBaseUrl,
  safeVaultPath,
  sha256Hex,
  stableEventId,
} from "./logic";
import { PublicationExecutor } from "./publication-executor";
import {
  KnowledgeIslandSettingTab,
  type BridgeSettingsController,
} from "./settings";
import {
  DEFAULT_PLUGIN_STATE,
  type ObsidianSyncEvent,
  type PendingPublication,
  type PluginState,
  type PublicationArtifactResult,
  type PublicationResultBatch,
  type SyncEventType,
} from "./types";

const EVENT_BATCH_SIZE = 50;
const MODIFY_DEBOUNCE_MS = 400;

export default class KnowledgeIslandPlugin
  extends Plugin
  implements BridgeSettingsController {
  state: PluginState = structuredClone(DEFAULT_PLUGIN_STATE);

  private api!: KnowledgeIslandApiClient;
  private publicationExecutor!: PublicationExecutor;
  private saveChain: Promise<void> = Promise.resolve();
  private eventFlushRunning = false;
  private resultFlushRunning = false;
  private publicationPollRunning = false;
  private runtimeStarted = false;
  private readonly modifyTimers = new Map<string, number>();
  private statusElement: HTMLElement | null = null;

  async onload(): Promise<void> {
    this.state = loadPluginState(await this.loadData());
    if (!this.state.vault_id) {
      this.state.vault_id = createVaultId(this.app.vault.getName());
      await this.persistState();
    }

    this.api = new KnowledgeIslandApiClient(
      () => this.state.backend_url,
      () => this.state.token,
    );
    this.publicationExecutor = new PublicationExecutor(
      this.app,
      () => this.normalizedOutputRoot(),
    );
    this.addSettingTab(new KnowledgeIslandSettingTab(this.app, this));
    this.statusElement = this.addStatusBarItem();
    this.updateStatus("待连接");

    this.app.workspace.onLayoutReady(() => {
      this.startRuntime();
    });
  }

  onunload(): void {
    for (const timer of this.modifyTimers.values()) {
      window.clearTimeout(timer);
    }
    this.modifyTimers.clear();
  }

  async saveConfiguration(input: {
    backend_url?: string;
    output_root?: string;
  }): Promise<void> {
    if (input.backend_url !== undefined) {
      this.state.backend_url = input.backend_url.trim();
    }
    if (input.output_root !== undefined && !this.state.token) {
      this.state.output_root = input.output_root.trim();
    }
    await this.persistState();
  }

  async completePairing(code: string): Promise<void> {
    const backendUrl = normalizeLoopbackBaseUrl(this.state.backend_url);
    const requestedRoot = this.state.output_root.trim()
      ? safeVaultPath(this.state.output_root, normalizePath)
      : undefined;
    this.state.backend_url = backendUrl;

    const response = await this.api.completePairing({
      code,
      vault_id: this.state.vault_id,
      vault_name: this.app.vault.getName(),
      output_root: requestedRoot,
    });
    const connection = response.connection;
    if (
      !connection.id
      || !connection.project_id
      || connection.vault_id !== this.state.vault_id
      || !response.token
    ) {
      throw new Error("Knowledge Island connection identity does not match this Vault.");
    }

    this.state.connection_id = connection.id;
    this.state.project_id = connection.project_id;
    this.state.token = response.token;
    this.state.output_root = safeVaultPath(connection.output_root, normalizePath);
    this.state.next_event_sequence = 1;
    this.state.event_queue = [];
    this.state.publication_result_queue = [];
    await this.persistState();
    this.updateStatus("已连接");

    await this.enqueueInitialVaultSnapshot();
    await this.synchronizeNow();
  }

  async revokeConnection(): Promise<void> {
    if (!this.state.token) {
      return;
    }
    await this.api.revokeConnection(this.state.connection_id);
    this.state.connection_id = "";
    this.state.project_id = "";
    this.state.token = "";
    this.state.next_event_sequence = 1;
    this.state.event_queue = [];
    this.state.publication_result_queue = [];
    await this.persistState();
    this.updateStatus("待连接");
  }

  async synchronizeNow(): Promise<void> {
    if (!this.state.token) {
      throw new Error("插件尚未配对。");
    }
    await this.flushPublicationResults();
    await this.flushEventQueue();
    await this.pollPendingPublications();
  }

  private startRuntime(): void {
    if (this.runtimeStarted) {
      return;
    }
    this.runtimeStarted = true;

    this.registerEvent(this.app.vault.on("create", (file) => {
      void this.onCreate(file);
    }));
    this.registerEvent(this.app.vault.on("modify", (file) => {
      this.onModify(file);
    }));
    this.registerEvent(this.app.vault.on("rename", (file, oldPath) => {
      void this.onRename(file, oldPath);
    }));
    this.registerEvent(this.app.vault.on("delete", (file) => {
      void this.onDelete(file);
    }));

    const intervalMilliseconds = Math.max(
      5,
      this.state.poll_interval_seconds,
    ) * 1000;
    this.registerInterval(window.setInterval(() => {
      void this.runBackgroundCycle();
    }, intervalMilliseconds));
    void this.runBackgroundCycle();
  }

  private async onCreate(file: TAbstractFile): Promise<void> {
    if (file instanceof TFile && file.extension.toLowerCase() === "md") {
      await this.captureFileEvent(file, "upsert");
    }
  }

  private onModify(file: TAbstractFile): void {
    if (!(file instanceof TFile) || file.extension.toLowerCase() !== "md") {
      return;
    }
    const scheduledPath = file.path;
    const previous = this.modifyTimers.get(scheduledPath);
    if (previous !== undefined) {
      window.clearTimeout(previous);
    }
    const timer = window.setTimeout(() => {
      this.modifyTimers.delete(scheduledPath);
      void this.captureFileEvent(file, "upsert");
    }, MODIFY_DEBOUNCE_MS);
    this.modifyTimers.set(scheduledPath, timer);
  }

  private async onRename(file: TAbstractFile, oldPath: string): Promise<void> {
    if (!this.state.token) {
      return;
    }
    this.clearModifyTimer(oldPath);
    this.clearModifyTimer(file.path);
    const oldMarkdown = oldPath.toLocaleLowerCase().endsWith(".md");
    const newMarkdown = file instanceof TFile && file.extension.toLowerCase() === "md";
    if (!oldMarkdown && !newMarkdown) {
      return;
    }

    const normalizedOld = safeVaultPath(oldPath, normalizePath);
    const normalizedNew = safeVaultPath(file.path, normalizePath);
    const outputRoot = this.normalizedOutputRoot();
    if (oldMarkdown && !newMarkdown) {
      if (!isPathInsideRoot(normalizedOld, outputRoot)) {
        await this.enqueueDelete(normalizedOld);
      }
      return;
    }
    if (!oldMarkdown && newMarkdown && file instanceof TFile) {
      await this.captureFileEvent(file, "upsert");
      return;
    }

    const route = classifyRename(normalizedOld, normalizedNew, outputRoot);
    if (route === "ignore") {
      return;
    }
    if (route === "delete") {
      await this.enqueueDelete(normalizedOld);
      return;
    }
    if (route === "upsert" && file instanceof TFile) {
      await this.captureFileEvent(file, "upsert");
      return;
    }
    if (file instanceof TFile) {
      await this.captureFileEvent(file, "rename", normalizedOld);
    }
  }

  private async onDelete(file: TAbstractFile): Promise<void> {
    this.clearModifyTimer(file.path);
    if (
      !this.state.token
      || !(file instanceof TFile)
      || file.extension.toLowerCase() !== "md"
    ) {
      return;
    }
    const path = safeVaultPath(file.path, normalizePath);
    if (!isPathInsideRoot(path, this.normalizedOutputRoot())) {
      await this.enqueueDelete(path);
    }
  }

  private async captureFileEvent(
    file: TFile,
    type: Extract<SyncEventType, "upsert" | "rename">,
    oldPath?: string,
  ): Promise<void> {
    if (!this.state.token) {
      return;
    }
    const path = safeVaultPath(file.path, normalizePath);
    if (isPathInsideRoot(path, this.normalizedOutputRoot())) {
      return;
    }

    try {
      const content = await this.app.vault.cachedRead(file);
      const metadata = this.app.metadataCache.getFileCache(file);
      await this.enqueueEvent({
        type,
        path,
        old_path: oldPath,
        content,
        content_hash: sha256Hex(content),
        frontmatter: cleanFrontmatter(metadata),
        tags: collectTags(metadata),
        resolved_links: cleanLinkCounts(
          this.app.metadataCache.resolvedLinks[path],
        ),
        unresolved_links: cleanLinkCounts(
          this.app.metadataCache.unresolvedLinks[path],
        ),
      });
    } catch {
      // A note can be renamed or deleted again before the asynchronous read completes.
      // The later Vault event is authoritative, so no synthetic event is emitted here.
    }
  }

  private async enqueueDelete(path: string): Promise<void> {
    await this.enqueueEvent({
      type: "delete",
      path,
      frontmatter: {},
      tags: [],
      resolved_links: {},
      unresolved_links: {},
    });
  }

  private async enqueueEvent(
    event: Omit<ObsidianSyncEvent, "event_id" | "occurred_at">,
  ): Promise<void> {
    const sequence = this.state.next_event_sequence;
    this.state.next_event_sequence += 1;
    this.state.event_queue.push({
      ...event,
      event_id: stableEventId(this.state.connection_id, sequence),
      occurred_at: new Date().toISOString(),
    });
    await this.persistState();
    void this.flushEventQueue();
  }

  private async enqueueInitialVaultSnapshot(): Promise<void> {
    for (const file of this.app.vault.getMarkdownFiles()) {
      if (
        !isPathInsideRoot(
          safeVaultPath(file.path, normalizePath),
          this.normalizedOutputRoot(),
        )
      ) {
        await this.captureFileEvent(file, "upsert");
      }
    }
  }

  private async flushEventQueue(): Promise<void> {
    if (this.eventFlushRunning || !this.state.token) {
      return;
    }
    this.eventFlushRunning = true;
    try {
      while (this.state.event_queue.length > 0 && this.state.token) {
        const batch = this.state.event_queue.slice(0, EVENT_BATCH_SIZE);
        const results = await this.api.sendEvents(batch);
        const acknowledged = new Set(results.map((item) => item.event_id));
        if (!batch.every((item) => acknowledged.has(item.event_id))) {
          throw new Error("Knowledge Island did not acknowledge the complete event batch.");
        }
        this.state.event_queue = this.state.event_queue.filter(
          (item) => !acknowledged.has(item.event_id),
        );
        await this.persistState();
      }
      this.updateStatus("已同步");
    } finally {
      this.eventFlushRunning = false;
    }
  }

  private async flushPublicationResults(): Promise<void> {
    if (this.resultFlushRunning || !this.state.token) {
      return;
    }
    this.resultFlushRunning = true;
    try {
      while (
        this.state.publication_result_queue.length > 0
        && this.state.token
      ) {
        const batch = this.state.publication_result_queue[0];
        await this.api.reportPublicationResult(batch);
        this.state.publication_result_queue.shift();
        await this.persistState();
      }
    } finally {
      this.resultFlushRunning = false;
    }
  }

  private async pollPendingPublications(): Promise<void> {
    if (this.publicationPollRunning || !this.state.token) {
      return;
    }
    this.publicationPollRunning = true;
    try {
      await this.flushPublicationResults();
      const pendingResultIds = new Set(
        this.state.publication_result_queue.map((batch) => batch.publication_id),
      );
      const publications = await this.api.pendingPublications();
      for (const publication of publications) {
        if (pendingResultIds.has(publication.id)) {
          continue;
        }
        const results = await this.executePublication(publication);
        const batch: PublicationResultBatch = {
          publication_id: publication.id,
          results,
        };
        this.state.publication_result_queue.push(batch);
        pendingResultIds.add(publication.id);
        await this.persistState();
        await this.flushPublicationResults();
      }
    } finally {
      this.publicationPollRunning = false;
    }
  }

  private async executePublication(
    publication: PendingPublication,
  ): Promise<PublicationArtifactResult[]> {
    if (publication.project_id !== this.state.project_id) {
      return publication.artifacts.map((artifact) => ({
        revision_id: artifact.revision_id,
        status: "conflict",
        error_code: "project_id_mismatch",
        message: "Queued publication belongs to a different project.",
      }));
    }

    const results: PublicationArtifactResult[] = [];
    for (const artifact of publication.artifacts) {
      results.push(await this.publicationExecutor.execute(publication, artifact));
    }
    return results;
  }

  private async runBackgroundCycle(): Promise<void> {
    if (!this.state.token) {
      this.updateStatus("待连接");
      return;
    }
    try {
      await this.synchronizeNow();
    } catch {
      this.updateStatus(
        `离线队列 ${this.state.event_queue.length + this.state.publication_result_queue.length}`,
      );
    }
  }

  private normalizedOutputRoot(): string {
    return safeVaultPath(this.state.output_root, normalizePath);
  }

  private clearModifyTimer(path: string): void {
    const timer = this.modifyTimers.get(path);
    if (timer !== undefined) {
      window.clearTimeout(timer);
      this.modifyTimers.delete(path);
    }
  }

  private persistState(): Promise<void> {
    const snapshot = JSON.parse(JSON.stringify(this.state)) as PluginState;
    const operation = this.saveChain.then(async () => {
      await this.saveData(snapshot);
    });
    this.saveChain = operation.catch(() => undefined);
    return operation;
  }

  private updateStatus(status: string): void {
    if (this.statusElement !== null) {
      this.statusElement.setText(`Knowledge Island：${status}`);
    }
  }
}

function loadPluginState(value: unknown): PluginState {
  const loaded = isRecord(value) ? value : {};
  return {
    backend_url: stringValue(loaded.backend_url, DEFAULT_PLUGIN_STATE.backend_url),
    vault_id: stringValue(loaded.vault_id, ""),
    connection_id: stringValue(loaded.connection_id, ""),
    project_id: stringValue(loaded.project_id, ""),
    token: stringValue(loaded.token, ""),
    output_root: stringValue(loaded.output_root, DEFAULT_PLUGIN_STATE.output_root),
    next_event_sequence: positiveInteger(
      loaded.next_event_sequence,
      DEFAULT_PLUGIN_STATE.next_event_sequence,
    ),
    event_queue: Array.isArray(loaded.event_queue)
      ? loaded.event_queue as ObsidianSyncEvent[]
      : [],
    publication_result_queue: Array.isArray(loaded.publication_result_queue)
      ? loaded.publication_result_queue as PublicationResultBatch[]
      : [],
    poll_interval_seconds: positiveInteger(
      loaded.poll_interval_seconds,
      DEFAULT_PLUGIN_STATE.poll_interval_seconds,
    ),
  };
}

function createVaultId(vaultName: string): string {
  const randomId = globalThis.crypto?.randomUUID?.();
  if (randomId) {
    return `vault-${randomId}`;
  }
  return `vault-${sha256Hex(`${vaultName}:${Date.now()}:${Math.random()}`).slice(0, 32)}`;
}

function cleanFrontmatter(
  metadata: CachedMetadata | null,
): Record<string, unknown> {
  if (!metadata?.frontmatter) {
    return {};
  }
  const cleaned: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(metadata.frontmatter)) {
    if (key !== "position") {
      cleaned[key] = cleanJsonValue(value);
    }
  }
  return cleaned;
}

function collectTags(metadata: CachedMetadata | null): string[] {
  if (metadata === null) {
    return [];
  }
  return Array.from(new Set(getAllTags(metadata) ?? [])).sort();
}

function cleanLinkCounts(
  value: Record<string, number> | undefined,
): Record<string, number> {
  if (!value) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(value)
      .filter((entry) => Number.isFinite(entry[1]) && entry[1] > 0)
      .sort(([left], [right]) => left.localeCompare(right)),
  );
}

function cleanJsonValue(value: unknown): unknown {
  if (
    value === null
    || typeof value === "string"
    || typeof value === "number"
    || typeof value === "boolean"
  ) {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(cleanJsonValue);
  }
  if (isRecord(value)) {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, cleanJsonValue(item)]),
    );
  }
  return String(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" ? value : fallback;
}

function positiveInteger(value: unknown, fallback: number): number {
  return Number.isSafeInteger(value) && Number(value) > 0
    ? Number(value)
    : fallback;
}
