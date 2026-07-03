import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const repoRoot = process.cwd().endsWith("frontend") ? resolve(process.cwd(), "..") : process.cwd();

function readRepoFile(path) {
  return readFileSync(resolve(repoRoot, path), "utf8");
}

describe("phase 2 neutral visual theme", () => {
  it("does not use the old green or blue accent palette in the main UI styles", () => {
    const inspectedStyles = [
      readRepoFile("frontend/src/styles.css"),
      readRepoFile("frontend/src/styles/tokens.css"),
      readRepoFile("frontend/src/components/LibraryModal.vue"),
      readRepoFile("docs/previews/phase2-frontend-preview/index.html"),
    ].join("\n");

    expect(inspectedStyles).not.toMatch(
      /#(?:2f8a68|0e7c70|0b5f56|e7f5f2|e6f4f1|f1f8f6|cfe6df|2f7d65|1f664f|63b99e|81d3b8|183a30|315f9c|e6edf7|8fb5ed|18283c)\b/i,
    );
  });
});
