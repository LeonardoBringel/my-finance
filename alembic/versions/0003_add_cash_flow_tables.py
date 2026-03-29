"""add cash flow tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-01-01 00:00:00.000000
"""
import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cash_flow_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "cash_flow_template_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["template_id"], ["cash_flow_templates.id"], ondelete="CASCADE"
        ),
    )

    op.create_table(
        "cash_flow_months",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id", "year", "month", name="uq_cash_flow_month_user_year_month"
        ),
    )

    op.create_table(
        "cash_flow_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("month_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["month_id"], ["cash_flow_months.id"], ondelete="CASCADE"
        ),
    )


def downgrade() -> None:
    op.drop_table("cash_flow_entries")
    op.drop_table("cash_flow_months")
    op.drop_table("cash_flow_template_items")
    op.drop_table("cash_flow_templates")
