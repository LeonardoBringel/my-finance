"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id',            sa.Integer(),  primary_key=True, autoincrement=True),
        sa.Column('username',      sa.Text(),     nullable=False, unique=True),
        sa.Column('password_hash', sa.Text(),     nullable=False),
        sa.Column('is_admin',      sa.Boolean(),  nullable=False, server_default='false'),
        sa.Column('created_at',    sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'categories',
        sa.Column('id',      sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name',    sa.Text(),    nullable=False),
        sa.Column('type',    sa.Text(),    nullable=False),
    )
    op.create_index('ix_categories_user_id', 'categories', ['user_id'])

    op.create_table(
        'transactions',
        sa.Column('id',                 sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id',            sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id',        sa.Integer(), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('date',               sa.Text(),    nullable=False),
        sa.Column('description',        sa.Text(),    nullable=True),
        sa.Column('value',              sa.Text(),    nullable=False),
        sa.Column('installment_group',  sa.Text(),    nullable=True),
        sa.Column('installment_number', sa.Integer(), nullable=True),
        sa.Column('installment_total',  sa.Integer(), nullable=True),
        sa.Column('created_at',         sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_category_id', 'transactions', ['category_id'])


def downgrade() -> None:
    op.drop_table('transactions')
    op.drop_table('categories')
    op.drop_table('users')
