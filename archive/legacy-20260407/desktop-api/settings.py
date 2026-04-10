from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"

API_HOST = "127.0.0.1"
API_PORT = 8008

DB_PATH = PROJECT_ROOT / "desktop" / "db" / "rag_desktop.db"
