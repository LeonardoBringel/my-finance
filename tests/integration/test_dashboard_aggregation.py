"""Testes de integração para TransactionsRepository.get_dashboard_data."""

import pytest

from repositories.categories_repository import CategoriesRepository
from repositories.transactions_repository import TransactionsRepository
from repositories.users_repository import UsersRepository

pytestmark = pytest.mark.integration


def _seed():
    """Cria um usuário 'alice' com categorias Salario (entrada) e Mercado (saida)."""
    uid = UsersRepository.create_user("alice", "pw")["id"]
    CategoriesRepository.create_category(uid, "Salario", "entrada")
    CategoriesRepository.create_category(uid, "Mercado", "saida")
    cats = {c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)}
    return uid, cats


def test_summary_single_month(db_session):
    """Resumo de um único mês: entradas, saidas, saldo e saldo_acumulado iguais ao mês."""
    uid, cats = _seed()
    TransactionsRepository.create_transaction(
        uid, cats["Salario"], "2026-03-10", "Pagamento", 5000.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-03-05", "Compra", 1200.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-03-20", "Compra extra", 300.0
    )

    data = TransactionsRepository.get_dashboard_data(uid, 2026, 3)
    summary = data["summary"]

    assert summary["entradas"] == pytest.approx(5000.0)
    assert summary["saidas"] == pytest.approx(1500.0)
    assert summary["saldo"] == pytest.approx(3500.0)
    assert summary["saldo_acumulado"] == pytest.approx(3500.0)
    assert summary["pct_installments"] == pytest.approx(0.0)


def test_saldo_acumulado_across_months(db_session):
    """Saldo acumulado soma meses <= mês selecionado, enquanto saldo mensal usa só o mês."""
    uid, cats = _seed()
    TransactionsRepository.create_transaction(
        uid, cats["Salario"], "2026-01-15", "Jan", 1000.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-02-15", "Fev", 200.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Salario"], "2026-03-15", "Mar", 500.0
    )

    data = TransactionsRepository.get_dashboard_data(uid, 2026, 3)
    summary = data["summary"]

    assert summary["entradas"] == pytest.approx(500.0)
    assert summary["saidas"] == pytest.approx(0.0)
    assert summary["saldo"] == pytest.approx(500.0)
    # acumulado: (1000 + 500) entradas - (200) saidas = 1300
    assert summary["saldo_acumulado"] == pytest.approx(1300.0)


def test_expenses_and_income_by_cat(db_session):
    """Totais por categoria ordenados desc; saidas separadas de entradas."""
    uid, cats = _seed()
    CategoriesRepository.create_category(uid, "Lazer", "saida")
    cats = {c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)}

    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-04-01", "Compra A", 400.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-04-10", "Compra B", 100.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Lazer"], "2026-04-12", "Cinema", 250.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Salario"], "2026-04-05", "Salario", 3000.0
    )

    data = TransactionsRepository.get_dashboard_data(uid, 2026, 4)

    assert data["expenses_by_cat"] == [
        {"category": "Mercado", "total": pytest.approx(500.0)},
        {"category": "Lazer", "total": pytest.approx(250.0)},
    ]
    assert data["income_by_cat"] == [
        {"category": "Salario", "total": pytest.approx(3000.0)},
    ]


def test_january_uses_prev_december(db_session):
    """Para janeiro, o mês anterior é dezembro do ano anterior (total_prev)."""
    uid, cats = _seed()
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2025-12-15", "Dezembro", 800.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-01-10", "Janeiro", 100.0
    )

    data = TransactionsRepository.get_dashboard_data(uid, 2026, 1)

    assert data["summary"]["saidas"] == pytest.approx(100.0)
    assert data["descriptions_by_cat"]["Mercado"]["total"] == pytest.approx(100.0)
    assert data["descriptions_by_cat"]["Mercado"]["total_prev"] == pytest.approx(800.0)
