"""Testes de integração para parcelamento em TransactionsRepository (installments)."""

import pytest

from repositories.categories_repository import CategoriesRepository
from repositories.transactions_repository import TransactionsRepository
from repositories.users_repository import UsersRepository

pytestmark = pytest.mark.integration


def _seed_user_and_category(name="Compras", type_="saida"):
    """Cria um usuário e uma categoria, retornando (user_id, category_id)."""
    user = UsersRepository.create_user("alice", "password")
    CategoriesRepository.create_category(user["id"], name, type_)
    cat = next(
        c
        for c in CategoriesRepository.list_categories(user["id"])
        if c["name"] == name
    )
    return user["id"], cat["id"]


def test_installments_create_n_rows(db_session):
    """create_transaction com installments=3 gera 3 parcelas mensais consecutivas."""
    uid, cid = _seed_user_and_category()
    TransactionsRepository.create_transaction(
        uid, cid, "2026-01-15", "Notebook", 1200.0, installments=3
    )

    rows = TransactionsRepository.list_transactions(uid)

    assert len(rows) == 3
    groups = {r["installment_group"] for r in rows}
    assert len(groups) == 1
    assert None not in groups
    assert {r["installment_number"] for r in rows} == {1, 2, 3}
    assert all(r["installment_total"] == 3 for r in rows)
    assert {r["date"] for r in rows} == {
        "2026-01-15",
        "2026-02-15",
        "2026-03-15",
    }
    assert all(r["value"] == 400.0 for r in rows)
    assert sum(r["value"] for r in rows) == pytest.approx(1200.0)


def test_installments_rounding(db_session):
    """Parcelamento com divisão não exata arredonda cada parcela e respeita fim de mês."""
    uid, cid = _seed_user_and_category()
    TransactionsRepository.create_transaction(
        uid, cid, "2026-01-31", "Curso", 100.0, installments=3
    )

    rows = TransactionsRepository.list_transactions(uid)

    assert len(rows) == 3
    assert all(r["value"] == 33.33 for r in rows)
    assert sum(r["value"] for r in rows) == pytest.approx(99.99)
    # relativedelta fixa para o último dia válido: 2026-02 tem 28 dias.
    assert {r["date"] for r in rows} == {
        "2026-01-31",
        "2026-02-28",
        "2026-03-31",
    }


def test_single_transaction_has_null_installment_fields(db_session):
    """Transação única (installments=1) não preenche campos de parcela."""
    uid, cid = _seed_user_and_category()
    TransactionsRepository.create_transaction(
        uid, cid, "2026-04-10", "Café", 9.5, installments=1
    )

    rows = TransactionsRepository.list_transactions(uid)

    assert len(rows) == 1
    row = rows[0]
    assert row["installment_group"] is None
    assert row["installment_number"] is None
    assert row["installment_total"] is None
    assert row["value"] == 9.5
    assert row["date"] == "2026-04-10"
