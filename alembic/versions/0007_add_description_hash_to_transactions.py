"""add description_hash to transactions

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-14 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "transactions", sa.Column("description_hash", sa.Text(), nullable=True)
    )
    op.create_index(
        "ix_transactions_cat_desc_hash",
        "transactions",
        ["category_id", "description_hash"],
    )

    # Backfill hash for all existing transactions with a description
    from utils.crypto import decrypt, hash_for_lookup

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, description FROM transactions"
            " WHERE description IS NOT NULL AND description != ''"
        )
    ).fetchall()
    for row in rows:
        plain = decrypt(row.description)
        if plain:
            conn.execute(
                sa.text("UPDATE transactions SET description_hash = :h WHERE id = :id"),
                {"h": hash_for_lookup(plain), "id": row.id},
            )


def downgrade():
    op.drop_index("ix_transactions_cat_desc_hash", table_name="transactions")
    op.drop_column("transactions", "description_hash")
