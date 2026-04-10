from dataclasses import dataclass, field
from typing import List


@dataclass
class QueryTask:
    task_type: str
    target_domains: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    question: str = ""
