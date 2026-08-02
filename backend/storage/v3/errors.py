"""Typed storage errors exposed to v3 application services."""


class V3StoreError(RuntimeError):
    pass


class V3DataGenerationMismatchError(V3StoreError):
    pass


class V3SchemaVersionError(V3StoreError):
    pass


class StoreNotInitializedError(V3StoreError):
    pass


class RecordNotFoundError(V3StoreError):
    pass


class StateConflictError(V3StoreError):
    pass


class IdempotencyConflictError(StateConflictError):
    pass


__all__ = [
    "IdempotencyConflictError",
    "RecordNotFoundError",
    "StateConflictError",
    "StoreNotInitializedError",
    "V3DataGenerationMismatchError",
    "V3SchemaVersionError",
    "V3StoreError",
]
