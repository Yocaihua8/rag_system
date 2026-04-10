# Legacy compatibility launcher.
# Keep this file as the stable user-facing entry, but route to the new Qt runtime.
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from desktop.app.bootstrap import run


if __name__ == "__main__":
    raise SystemExit(run())

