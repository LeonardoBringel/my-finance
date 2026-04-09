"""add year column to transactions

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-09 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("transactions", sa.Column("year", sa.Integer(), nullable=True))
    op.create_index("ix_transactions_user_year", "transactions", ["user_id", "year"])

    # Backfill year for all existing transactions
    from utils.crypto import decrypt

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, date FROM transactions")).fetchall()
    for row in rows:
        plain = decrypt(row.date)
        try:
            year = int(plain[:4])
        except (ValueError, TypeError):
            continue
        conn.execute(
            sa.text("UPDATE transactions SET year = :y WHERE id = :id"),
            {"y": year, "id": row.id},
        )


def downgrade():
    op.drop_index("ix_transactions_user_year", table_name="transactions")
    op.drop_column("transactions", "year")
