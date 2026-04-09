"""add missing columns and indexes for query performance

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-09 00:00:00.000000

Note: migrations 0004 and 0005 were stamped but never applied to this database.
      This migration applies everything that was missing from those two plus the
      new indexes identified in the performance review.
"""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ── From 0004: add year column to transactions ─────────────────────────────
    op.add_column("transactions", sa.Column("year", sa.Integer(), nullable=True))

    from utils.crypto import decrypt

    rows = conn.execute(sa.text("SELECT id, date FROM transactions")).fetchall()
    for row in rows:
        try:
            plain_date = decrypt(row.date)
            year = int(plain_date[:4])
            conn.execute(
                sa.text("UPDATE transactions SET year = :y WHERE id = :id"),
                {"y": year, "id": row.id},
            )
        except Exception:
            pass

    # ── From 0005: add username_hash column to users ───────────────────────────
    op.add_column("users", sa.Column("username_hash", sa.Text(), nullable=True))

    from utils.crypto import hash_for_lookup

    rows = conn.execute(sa.text("SELECT id, username FROM users")).fetchall()
    for row in rows:
        try:
            plain = decrypt(row.username)
            conn.execute(
                sa.text("UPDATE users SET username_hash = :h WHERE id = :id"),
                {"h": hash_for_lookup(plain), "id": row.id},
            )
        except Exception:
            pass

    # ── New indexes ────────────────────────────────────────────────────────────
    op.create_index("ix_users_username_hash", "users", ["username_hash"], unique=True)

    # ix_transactions_user_year: composite covering the main filter pattern
    op.create_index("ix_transactions_user_year", "transactions", ["user_id", "year"])

    # ix_categories_user_id and ix_transactions_category_id already exist in DB
    # (created outside Alembic), so they are skipped here

    op.create_index(
        "ix_cash_flow_months_user_year", "cash_flow_months", ["user_id", "year"]
    )
    op.create_unique_constraint(
        "uq_cash_flow_months_user_year_month",
        "cash_flow_months",
        ["user_id", "year", "month"],
    )
    op.create_index("ix_cash_flow_entries_month_id", "cash_flow_entries", ["month_id"])
    op.create_index(
        "ix_cash_flow_template_items_template_id",
        "cash_flow_template_items",
        ["template_id"],
    )


def downgrade():
    op.drop_index(
        "ix_cash_flow_template_items_template_id",
        table_name="cash_flow_template_items",
    )
    op.drop_index("ix_cash_flow_entries_month_id", table_name="cash_flow_entries")
    op.drop_constraint(
        "uq_cash_flow_months_user_year_month", "cash_flow_months", type_="unique"
    )
    op.drop_index("ix_cash_flow_months_user_year", table_name="cash_flow_months")
    op.drop_index("ix_transactions_user_year", table_name="transactions")
    op.drop_index("ix_users_username_hash", table_name="users")
    op.drop_column("users", "username_hash")
    op.drop_column("transactions", "year")
