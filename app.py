"""Knowledge Island default launcher."""
import sys
from pathlib import Path

# 确保项目根在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.api.server import app, run_server

if __name__ == "__main__":
    raise SystemExit(run_server())
