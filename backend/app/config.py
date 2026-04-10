from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(r"F:\PersonalRAG")

KNOWLEDGE_BASE_PATH = DATA_ROOT / "knowledge_base"
RAW_PATH = KNOWLEDGE_BASE_PATH / "raw"
PROCESSED_PATH = KNOWLEDGE_BASE_PATH / "processed"
CHUNKS_PATH = KNOWLEDGE_BASE_PATH / "chunks"
METADATA_PATH = KNOWLEDGE_BASE_PATH / "metadata"
EXPORT_PATH = KNOWLEDGE_BASE_PATH / "exports"

INDEXES_PATH = DATA_ROOT / "indexes"
VECTOR_INDEX_PATH = INDEXES_PATH / "vector"
KEYWORD_INDEX_PATH = INDEXES_PATH / "keyword"

BACKUP_PATH = DATA_ROOT / "backups"
TEMP_PATH = DATA_ROOT / "temp"

REQUIRED_DIRS = [
    PROJECT_ROOT / "backend" / "app",
    PROJECT_ROOT / "scripts",
#    PROJECT_ROOT / "templates",
    PROJECT_ROOT / "backend" / "tests",
    KNOWLEDGE_BASE_PATH,
    RAW_PATH,
    PROCESSED_PATH,
    CHUNKS_PATH,
    METADATA_PATH,
    EXPORT_PATH,
    VECTOR_INDEX_PATH,
    KEYWORD_INDEX_PATH,
    BACKUP_PATH,
    TEMP_PATH,
    RAW_PATH / "resume",
    RAW_PATH / "jds",
    RAW_PATH / "notes",
    RAW_PATH / "paper",
    RAW_PATH / "prompts",
    RAW_PATH / "archive",
]

# Maturity priority for sorting drafts. Lower is higher priority.
MATURITY_PRIORITY = {
    "已上线": 1,
    "生产": 1,
    "稳定": 2,
    "可用": 3,
    "持续优化": 4,
    "持续迭代": 4,
    "mvp": 5,
    "草稿": 6,
    "draft": 6,
}


def ensure_storage_dirs() -> None:
    for path in REQUIRED_DIRS:
        path.mkdir(parents=True, exist_ok=True)
