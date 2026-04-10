import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.app.config import REQUIRED_DIRS


def main() -> None:
    created = 0
    for path in REQUIRED_DIRS:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created += 1
            print(f"[CREATE] {path}")
        else:
            print(f"[EXISTS] {path}")
    print(f"[DONE] created={created}, checked={len(REQUIRED_DIRS)}")


if __name__ == "__main__":
    main()
