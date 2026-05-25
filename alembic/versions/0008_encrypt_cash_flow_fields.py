"""encrypt cash_flow name and value fields

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-23 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

_TABLES = ("cash_flow_entries", "cash_flow_template_items")


def _enc(value):
    """Encripta um valor apenas se ainda não for ciphertext (idempotente)."""
    from utils.crypto import decrypt, encrypt

    if value is None or value == "":
        return value
    # decrypt() retorna o próprio token em texto plano quando o Fernet falha;
    # se o valor decriptado difere do original, já está encriptado → pular.
    if decrypt(value) != value:
        return value
    return encrypt(value)


def _dec(value):
    """Descriptografa um valor de volta para texto plano (downgrade)."""
    from utils.crypto import decrypt

    if value is None or value == "":
        return value
    return decrypt(value)


def upgrade():
    # 1) value: Numeric(12,2) -> Text (preserva o número como string)
    for table in _TABLES:
        op.alter_column(
            table,
            "value",
            existing_type=sa.Numeric(12, 2),
            type_=sa.Text(),
            existing_nullable=False,
            postgresql_using="value::text",
        )

    # 2) Encripta name e value de todas as linhas (idempotente)
    conn = op.get_bind()
    for table in _TABLES:
        rows = conn.execute(
            sa.text(f"SELECT id, name, value FROM {table}")
        ).fetchall()
        for row in rows:
            conn.execute(
                sa.text(
                    f"UPDATE {table} SET name = :n, value = :v WHERE id = :id"
                ),
                {"n": _enc(row.name), "v": _enc(row.value), "id": row.id},
            )


def downgrade():
    # 1) Descriptografa name e value de volta para texto plano
    conn = op.get_bind()
    for table in _TABLES:
        rows = conn.execute(
            sa.text(f"SELECT id, name, value FROM {table}")
        ).fetchall()
        for row in rows:
            conn.execute(
                sa.text(
                    f"UPDATE {table} SET name = :n, value = :v WHERE id = :id"
                ),
                {"n": _dec(row.name), "v": _dec(row.value), "id": row.id},
            )

    # 2) value: Text -> Numeric(12,2)
    for table in _TABLES:
        op.alter_column(
            table,
            "value",
            existing_type=sa.Text(),
            type_=sa.Numeric(12, 2),
            existing_nullable=False,
            postgresql_using="value::numeric",
        )
