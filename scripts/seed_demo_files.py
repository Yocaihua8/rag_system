# -*- coding: utf-8 -*-
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.app.config import RAW_PATH


SEED_CONTENT = {
    RAW_PATH / "resume" / "resume_master.md": """# Resume Master

## Personal Info
- Name: <Your Name>
- Contact: <Phone / Email>
- City: <City>

## Target Role
- Python RAG Engineer / Backend-focused AI Assistant

## Skills
- Backend: Python, FastAPI
- Database: SQLite
- Frontend: Vue3

## RAG Summary
- End-to-end workflow for import, chunking, indexing, retrieval, and answer generation.
""",
    RAW_PATH / "resume" / "project_bullets.md": """# Project Bullets

## Business Loop
- [Role] Python Backend
  [Tags] python, fastapi, rag
  [Maturity] Production
  [Updated] 2026-04-05
  [Bullet] Built local RAG processing flow from markdown import to retrieval-ready chunk storage.

## Draft Flow
- [Role] Python Backend
  [Tags] draft, fastapi, vue
  [Maturity] Stable
  [Updated] 2026-04-05
  [Bullet] Added draft save and re-edit flow for prompt templates and notes.

## API Stability
- [Role] Python Backend
  [Tags] api, fastapi, sqlite
  [Maturity] Iterating
  [Updated] 2026-04-05
  [Bullet] Standardized API request validation and error handling for desktop integration.

## Retrieval Quality
- [Role] Python Backend
  [Tags] retrieval, rag, sqlite
  [Maturity] Production
  [Updated] 2026-04-05
  [Bullet] Improved retrieval hit precision with domain-aware tags and consistent chunk generation.

## OCR + FastAPI
- [Role] Python Backend
  [Tags] python, fastapi, api
  [Maturity] MVP
  [Updated] 2026-04-05
  [Bullet] Integrated local service orchestration for import and retrieval pipeline tasks.

## Export & Print
- [Role] Fullstack
  [Tags] export, vue, fastapi
  [Maturity] Stable
  [Updated] 2026-04-05
  [Bullet] Added export capability for RAG outputs and debugging snapshots.

## Debug & Integration
- [Role] Python Backend
  [Tags] fastapi, api, retrieval
  [Maturity] Ongoing
  [Updated] 2026-04-05
  [Bullet] Diagnosed path/method/field/response mismatches to speed up frontend-backend integration.
""",
    RAW_PATH / "resume" / "project_updates.md": """# Project Updates Log

## Entry Template
- Date:
- Module:
- Change Type:
- Background:
- Changes:
- API Impact:
- Field Impact:
- Risk / Rollback:
- Validation:
- Tags:

## 2026-04-05
- Date: 2026-04-05
- Module: RAG MVP scaffold
- Change Type: Initialization
- Background: Missing reusable structure for resume/project knowledge retrieval.
- Changes: Created project skeleton, storage layout, and CLI demo flow.
- API Impact: None
- Field Impact: domain, tags, status, importance
- Risk / Rollback: Low; file-level rollback is enough.
- Validation: Directory init, seed files, and demo generation executed.
- Tags: python, fastapi, draft, export
""",
    RAW_PATH / "jds" / "jd_library.md": """# JD Library

## JD Template
- Job Title:
- Direction:
- Keywords:
- Original JD:
- Match Notes:

## JD-001
- Job Title: RAG Engineer
- Direction: Python RAG
- Keywords: Python, FastAPI, RAG, retrieval, API design, performance
- Original JD:
  1. Build and maintain local RAG assistant pipelines.
  2. Design APIs and troubleshoot desktop integration issues.
  3. Collaborate with frontend for end-to-end feature delivery.
- Match Notes: Highlight import/build/query flow, retrieval quality, and integration debugging.
""",
    RAW_PATH / "notes" / "notes_overview.md": """# RAG Notes Overview

## Background
- Improve personal knowledge retrieval quality and local desktop experience.

## Core Modules
- Document Import
- Chunking and Index Build
- Retrieval and Query
- Draft / Export
- FastAPI + pywebview integration

## Stack
- Python, FastAPI, SQLite, Vue3, pywebview

## Current Stage
- Core workflow ready; integration and stability are improving.

## Talking Points
- End-to-end RAG flow closure
- Interface alignment and debugging efficiency
- Local desktop integration with Python-first runtime

## Next Plan
- Add automated tests for critical APIs.
- Upgrade to vector retrieval and rerank.
""",
}


def main() -> None:
    for path, content in SEED_CONTENT.items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print("[CREATE] {0}".format(path))
        else:
            print("[SKIP] {0}".format(path))


if __name__ == "__main__":
    main()
