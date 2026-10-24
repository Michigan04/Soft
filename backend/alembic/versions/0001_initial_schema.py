"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-20

NOTE: This initial migration uses SQLAlchemy's declarative metadata
(Base.metadata.create_all/drop_all) rather than hand-written op.create_table
calls or `alembic revision --autogenerate`. Autogeneration requires a live,
reachable PostgreSQL instance, which was not available in the environment
this migration was authored in (no Docker, no working local PostgreSQL
install). Driving create_all/drop_all from within a migration still produces
correct PostgreSQL DDL (native ENUM types, UUID columns, etc.) from the same
models used by the application, and is tracked by Alembic like any other
migration. Future schema changes should use `alembic revision --autogenerate`
against a running database so incremental diffs are captured normally.
"""
from typing import Sequence, Union

from alembic import op

from app.db.base import Base
from app.models import *  # noqa: F401,F403 - registers all tables on Base.metadata

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
