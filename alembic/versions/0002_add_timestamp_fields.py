"""add updated_at to all tables and created_at to categories

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-01 00:00:00.000000
"""
import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── categories ────────────────────────────────────────────────────────────
    op.add_column(
        "categories",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "categories",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── transactions ──────────────────────────────────────────────────────────
    op.add_column(
        "transactions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("transactions", "updated_at")
    op.drop_column("categories", "updated_at")
    op.drop_column("categories", "created_at")
    op.drop_column("users", "updated_at")
