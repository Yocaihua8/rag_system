from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    PAUSED = "paused"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    RECOVERY_REQUIRED = "recovery_required"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ArtifactStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    EXPORTED = "exported"
    FAILED = "failed"


class DepthProfile(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class EffectKind(StrEnum):
    NONE = "none"
    READ = "read"
    ANALYSIS = "analysis"
    PROJECT_WRITE = "project_write"
    EXTERNAL_WRITE = "external_write"

    @property
    def requires_approval(self) -> bool:
        return self in {self.PROJECT_WRITE, self.EXTERNAL_WRITE}


@dataclass(frozen=True, slots=True)
class DepthLimits:
    max_steps: int
    max_tool_iterations: int

    def __post_init__(self) -> None:
        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")
        if self.max_tool_iterations < 1:
            raise ValueError("max_tool_iterations must be positive")


DEPTH_LIMITS: Mapping[DepthProfile, DepthLimits] = MappingProxyType(
    {
        DepthProfile.QUICK: DepthLimits(max_steps=4, max_tool_iterations=1),
        DepthProfile.STANDARD: DepthLimits(max_steps=8, max_tool_iterations=3),
        DepthProfile.DEEP: DepthLimits(max_steps=16, max_tool_iterations=6),
    }
)


def get_depth_limits(profile: DepthProfile | str) -> DepthLimits:
    try:
        normalized = profile if isinstance(profile, DepthProfile) else DepthProfile(profile)
    except ValueError as exc:
        raise ValueError(f"unknown depth profile: {profile}") from exc
    return DEPTH_LIMITS[normalized]
