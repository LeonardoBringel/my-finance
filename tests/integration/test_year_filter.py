"""Testes de integração para o filtro de ano por SQL em list_transactions.

Cobrem PERF-01: o predicado `Transaction.year == year` é empurrado para o SQL
(usando o índice ix_transactions_user_year) em vez de filtrar após descriptografar,
preservando o comportamento anterior.
"""

from datetime import datetime

import pytest

from models import Transaction
from repositories.base_repository import get_session
from repositories.categories_repository import CategoriesRepository
from repositories.transactions_repository import TransactionsRepository
from repositories.users_repository import UsersRepository
from utils.crypto import encrypt

pytestmark = pytest.mark.integration


def _seed_multi_year(db_session):
    """Cria 'alice' com categorias e transações espalhadas por três anos."""
    uid = UsersRepository.create_user("alice", "password")["id"]
    CategoriesRepository.create_category(uid, "Salario", "entrada")
    CategoriesRepository.create_category(uid, "Mercado", "saida")
    cats = {c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)}

    TransactionsRepository.create_transaction(
        uid, cats["Salario"], "2024-05-10", "2024 A", 1000.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2024-08-01", "2024 B", 200.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Salario"], "2025-03-15", "2025 A", 1500.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-01-20", "2026 A", 300.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-07-09", "2026 B", 450.0
    )
    return uid, cats


def test_year_filter_matches_python_filter(db_session):
    """Resultados filtrados por ano no SQL == filtrar todas as linhas em Python por ano."""
    uid, _ = _seed_multi_year(db_session)

    all_txns = TransactionsRepository.list_transactions(uid)
    expected = [
        t for t in all_txns if datetime.strptime(t["date"], "%Y-%m-%d").year == 2026
    ]

    got = TransactionsRepository.list_transactions(uid, year=2026)

    assert got == expected
    assert {t["description"] for t in got} == {"2026 A", "2026 B"}


def test_no_year_returns_all_years(db_session):
    """Sem ano informado, todas as transações de todos os anos são retornadas."""
    uid, _ = _seed_multi_year(db_session)

    got = TransactionsRepository.list_transactions(uid)

    assert len(got) == 5
    assert {datetime.strptime(t["date"], "%Y-%m-%d").year for t in got} == {
        2024,
        2025,
        2026,
    }


def test_year_with_month_filter_still_applies(db_session):
    """Filtro de mês (em Python) continua valendo junto com o filtro de ano (SQL)."""
    uid, _ = _seed_multi_year(db_session)

    got = TransactionsRepository.list_transactions(uid, year=2026, month=7)

    assert len(got) == 1
    assert got[0]["description"] == "2026 B"


def test_filters_by_year_column_not_decrypted_date(db_session):
    """O filtro usa a coluna SQL `year`, não o ano da data descriptografada.

    Insere uma linha deliberadamente inconsistente (data 2025, coluna year=2026).
    Em produção year é sempre derivado da data, então isso não ocorre — mas prova
    que o predicado é aplicado no SQL sobre a coluna indexada.
    """
    uid, cats = _seed_multi_year(db_session)

    with get_session() as s:
        s.add(
            Transaction(
                user_id=uid,
                category_id=cats["Mercado"],
                date=encrypt("2025-06-01"),
                year=2026,
                value=encrypt("99.0"),
            )
        )
        s.commit()

    got_2026 = TransactionsRepository.list_transactions(uid, year=2026)
    got_2025 = TransactionsRepository.list_transactions(uid, year=2025)

    dates_2026 = {t["date"] for t in got_2026}
    assert "2025-06-01" in dates_2026  # incluída pelo year=2026 (coluna)
    assert "2025-06-01" not in {t["date"] for t in got_2025}


def test_null_year_legacy_row_excluded_from_year_view(db_session):
    """Linha legada com year NULL (data não-parseável) é excluída da visão por ano.

    Espelha o comportamento anterior (o guard de strptime já as excluía) — AC P1-1-4.
    """
    uid, cats = _seed_multi_year(db_session)

    with get_session() as s:
        s.add(
            Transaction(
                user_id=uid,
                category_id=cats["Mercado"],
                date=encrypt("data-invalida"),
                year=None,
                value=encrypt("10.0"),
            )
        )
        s.commit()

    got_2026 = TransactionsRepository.list_transactions(uid, year=2026)
    got_all = TransactionsRepository.list_transactions(uid)

    # Excluída da visão por ano (year NULL não casa) e da visão geral (strptime falha).
    assert all(t["date"] != "data-invalida" for t in got_2026)
    assert all(t["date"] != "data-invalida" for t in got_all)
