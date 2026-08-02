"""Create the isolated v3 Agent schema.

Revision ID: 0001_v3_initial
Revises: None
Create Date: 2026-08-02
"""
from __future__ import annotations

from datetime import datetime, timezone

from alembic import op

from backend.storage.v3.schema import app_metadata, metadata


revision = "0001_v3_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    metadata.create_all(bind=bind)
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )
    op.bulk_insert(
        app_metadata,
        [
            {"key": "data_generation", "value": "v3", "updated_at": now},
            {"key": "schema_version", "value": revision, "updated_at": now},
        ],
    )


def downgrade() -> None:
    metadata.drop_all(bind=op.get_bind())
