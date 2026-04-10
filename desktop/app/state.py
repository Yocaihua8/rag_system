from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppState:
    ready: bool = False
