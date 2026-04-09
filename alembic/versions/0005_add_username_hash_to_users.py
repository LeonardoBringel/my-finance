"""add username_hash to users

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-09 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("username_hash", sa.Text(), nullable=True))
    op.create_index("ix_users_username_hash", "users", ["username_hash"], unique=True)

    # Backfill hash for all existing users
    from utils.crypto import decrypt, hash_for_lookup

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, username FROM users")).fetchall()
    for row in rows:
        plain = decrypt(row.username)
        conn.execute(
            sa.text("UPDATE users SET username_hash = :h WHERE id = :id"),
            {"h": hash_for_lookup(plain), "id": row.id},
        )


def downgrade():
    op.drop_index("ix_users_username_hash", table_name="users")
    op.drop_column("users", "username_hash")
