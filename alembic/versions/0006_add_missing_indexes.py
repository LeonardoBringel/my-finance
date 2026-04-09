"""add missing indexes for query performance

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-09 00:00:00.000000
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
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
