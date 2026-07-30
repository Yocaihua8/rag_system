import {
  App,
  normalizePath,
  TFile,
  TFolder,
} from "obsidian";

import {
  assertManagedMetadata,
  BridgeConflict,
  expectedManagedMetadata,
  managedMetadataFromContent,
  sha256Hex,
  validatePublicationPath,
} from "./logic";
import type {
  ManagedMetadata,
  PendingPublication,
  PublicationArtifact,
  PublicationArtifactResult,
} from "./types";

export class PublicationExecutor {
  constructor(
    private readonly app: App,
    private readonly outputRoot: () => string,
  ) {}

  async execute(
    publication: PendingPublication,
    artifact: PublicationArtifact,
  ): Promise<PublicationArtifactResult> {
    let actualHash: string | undefined;
    try {
      const targetPath = validatePublicationPath(
        artifact.target_path,
        this.outputRoot(),
        normalizePath,
      );
      if (sha256Hex(artifact.content) !== artifact.content_hash) {
        throw new BridgeConflict(
          "content_hash_mismatch",
          "Publication content does not match the confirmed hash.",
        );
      }

      const expected = expectedManagedMetadata(publication, artifact);
      const proposedMetadata = managedMetadataFromContent(artifact.content);
      assertManagedMetadata(proposedMetadata, expected);
      assertRevision(proposedMetadata, expected);

      const existing = this.app.vault.getAbstractFileByPath(targetPath);
      let target: TFile;
      if (existing === null) {
        await this.ensureParentFolder(targetPath);
        try {
          target = await this.app.vault.create(targetPath, artifact.content);
        } catch (error) {
          const raced = this.app.vault.getAbstractFileByPath(targetPath);
          if (raced !== null) {
            throw new BridgeConflict(
              "target_exists",
              "Publication target was created before the confirmed write.",
            );
          }
          throw error;
        }
      } else {
        if (!(existing instanceof TFile)) {
          throw new BridgeConflict(
            "target_type_conflict",
            "Publication target exists but is not a file.",
          );
        }
        target = existing;
        const expectedVaultHash = String(artifact.expected_vault_hash ?? "").trim();
        if (!expectedVaultHash) {
          throw new BridgeConflict(
            "expected_vault_hash_required",
            "An existing target requires a confirmed Vault hash.",
          );
        }

        await this.app.vault.process(target, (currentContent) => {
          if (sha256Hex(currentContent) !== expectedVaultHash) {
            throw new BridgeConflict(
              "vault_hash_conflict",
              "The target changed after publication preview.",
            );
          }
          assertManagedMetadata(managedMetadataFromContent(currentContent), expected);
          return artifact.content;
        });
      }

      await this.applyAndVerifyManagedFrontmatter(target, expected);
      const finalContent = await this.app.vault.read(target);
      assertManagedMetadata(managedMetadataFromContent(finalContent), expected);
      assertRevision(managedMetadataFromContent(finalContent), expected);
      actualHash = sha256Hex(finalContent);

      return {
        revision_id: artifact.revision_id,
        status: "applied",
        actual_hash: actualHash,
      };
    } catch (error) {
      if (error instanceof BridgeConflict) {
        return {
          revision_id: artifact.revision_id,
          status: "conflict",
          actual_hash: actualHash,
          error_code: error.code,
          message: error.message,
        };
      }
      return {
        revision_id: artifact.revision_id,
        status: "failed",
        actual_hash: actualHash,
        error_code: "plugin_execution_failed",
        message: safeErrorMessage(error),
      };
    }
  }

  private async applyAndVerifyManagedFrontmatter(
    file: TFile,
    expected: ManagedMetadata,
  ): Promise<void> {
    await this.app.fileManager.processFrontMatter(file, (frontmatter) => {
      frontmatter.knowledge_island_managed = true;
      frontmatter.knowledge_island_id = expected.knowledge_island_id;
      frontmatter.knowledge_island_project_id = expected.knowledge_island_project_id;
      frontmatter.knowledge_island_artifact_type = expected.knowledge_island_artifact_type;
      frontmatter.knowledge_island_revision = expected.knowledge_island_revision;
    });

    const finalContent = await this.app.vault.read(file);
    const actual = managedMetadataFromContent(finalContent);
    assertManagedMetadata(actual, expected);
    assertRevision(actual, expected);
  }

  private async ensureParentFolder(path: string): Promise<void> {
    const separator = path.lastIndexOf("/");
    if (separator < 0) {
      return;
    }

    const parts = path.slice(0, separator).split("/");
    let current = "";
    for (const part of parts) {
      current = current ? `${current}/${part}` : part;
      const existing = this.app.vault.getAbstractFileByPath(current);
      if (existing instanceof TFile) {
        throw new BridgeConflict(
          "parent_path_conflict",
          "A parent path exists as a file.",
        );
      }
      if (existing === null) {
        try {
          await this.app.vault.createFolder(current);
        } catch (error) {
          const raced = this.app.vault.getAbstractFileByPath(current);
          if (!(raced instanceof TFolder)) {
            throw error;
          }
        }
      }
    }
  }
}

function assertRevision(
  actual: Record<string, unknown>,
  expected: ManagedMetadata,
): void {
  if (
    Number(actual.knowledge_island_revision)
    !== expected.knowledge_island_revision
  ) {
    throw new BridgeConflict(
      "revision_mismatch",
      "Managed publication revision does not match.",
    );
  }
}

function safeErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message.slice(0, 500);
  }
  return "Unknown plugin execution error.";
}
