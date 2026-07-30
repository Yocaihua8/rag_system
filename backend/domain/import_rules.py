from pathlib import PurePath


TEXT_SUFFIXES = {
    ".cfg",
    ".cjs",
    ".css",
    ".docx",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".pdf",
    ".py",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".yaml",
    ".yml",
}

TEXT_FILE_NAMES = {
    "dockerfile",
    "makefile",
}

IGNORED_DIR_NAMES = {
    ".agents",
    ".claude",
    ".codex",
    ".git",
    ".hg",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".vscode",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "__pycache__",
}

MAX_TEXT_FILE_BYTES = 1_000_000


def is_supported_text_path(path: str | PurePath) -> bool:
    candidate = PurePath(path)
    name = candidate.name.lower()
    return (
        candidate.suffix.lower() in TEXT_SUFFIXES
        or name in TEXT_FILE_NAMES
        or name.startswith("dockerfile.")
    )
