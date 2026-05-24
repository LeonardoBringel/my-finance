"""add token_version to users

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-23 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("users", "token_version")
