"""Testes de integração para TransactionsRepository.get_dashboard_data."""

import pytest

from repositories.categories_repository import CategoriesRepository
from repositories.transactions_repository import TransactionsRepository
from repositories.users_repository import UsersRepository

pytestmark = pytest.mark.integration


def _seed():
    """Cria um usuário 'alice' com categorias Salario (entrada) e Mercado (saida)."""
    uid = UsersRepository.create_user("alice", "password")["id"]
    CategoriesRepository.create_category(uid, "Salario", "entrada")
    CategoriesRepository.create_category(uid, "Mercado", "saida")
    cats = {
        c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)
    }
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
    cats = {
        c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)
    }

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
    assert data["descriptions_by_cat"]["Mercado"]["total"] == pytest.approx(
        100.0
    )
    assert data["descriptions_by_cat"]["Mercado"][
        "total_prev"
    ] == pytest.approx(800.0)


def test_investment_out_of_saidas_and_saldo(db_session):
    """Aporte soma em investimentos sem tocar saidas, saldo nem saldo_acumulado."""
    uid, cats = _seed()
    CategoriesRepository.create_category(uid, "Tesouro", "investimento")
    cats = {
        c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)
    }

    TransactionsRepository.create_transaction(
        uid, cats["Salario"], "2026-05-05", "Pagamento", 1000.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-05-10", "Compra", 500.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Tesouro"], "2026-05-15", "Aporte", 200.0
    )

    summary = TransactionsRepository.get_dashboard_data(uid, 2026, 5)["summary"]

    assert summary["saidas"] == pytest.approx(500.0)
    assert summary["investimentos"] == pytest.approx(200.0)
    assert summary["saldo"] == pytest.approx(500.0)
    assert summary["saldo_acumulado"] == pytest.approx(500.0)


def test_investment_absent_from_income_and_expense_views(db_session):
    """Aporte não aparece em income_by_cat, expenses_by_cat nem expenses_by_day_cat."""
    uid, cats = _seed()
    CategoriesRepository.create_category(uid, "Tesouro", "investimento")
    cats = {
        c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)
    }

    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-05-10", "Compra", 500.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Tesouro"], "2026-05-15", "Aporte", 200.0
    )

    data = TransactionsRepository.get_dashboard_data(uid, 2026, 5)

    income_cats = {row["category"] for row in data["income_by_cat"]}
    expense_cats = {row["category"] for row in data["expenses_by_cat"]}
    assert "Tesouro" not in income_cats
    assert "Tesouro" not in expense_cats
    assert "Tesouro" not in data["expenses_by_day_cat"]


def test_annual_carries_investment(db_session):
    """O mês no grid anual traz investimento sem alterar saldo_acumulado."""
    uid, cats = _seed()
    CategoriesRepository.create_category(uid, "Tesouro", "investimento")
    cats = {
        c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)
    }

    TransactionsRepository.create_transaction(
        uid, cats["Salario"], "2026-05-05", "Pagamento", 1000.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Mercado"], "2026-05-10", "Compra", 500.0
    )
    TransactionsRepository.create_transaction(
        uid, cats["Tesouro"], "2026-05-15", "Aporte", 200.0
    )

    annual = TransactionsRepository.get_dashboard_data(uid, 2026, 5)["annual"]
    may = next(m for m in annual if m["month"] == "05")

    assert may["investimento"] == pytest.approx(200.0)
    assert may["saldo_acumulado"] == pytest.approx(500.0)


def test_descriptions_include_investment_with_type(db_session):
    """descriptions_by_cat inclui a categoria de investimento com type 'investimento'."""
    uid, cats = _seed()
    CategoriesRepository.create_category(uid, "Tesouro", "investimento")
    cats = {
        c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)
    }

    TransactionsRepository.create_transaction(
        uid, cats["Tesouro"], "2026-05-15", "Aporte", 200.0
    )

    detail = TransactionsRepository.get_dashboard_data(uid, 2026, 5)[
        "descriptions_by_cat"
    ]

    assert "Tesouro" in detail
    assert detail["Tesouro"]["type"] == "investimento"
    assert detail["Tesouro"]["total"] == pytest.approx(200.0)


def test_pct_of_month_investment_only(db_session):
    """Mês só com aporte: pct_of_month da categoria de investimento é 100%, sem divisão por zero."""
    uid, cats = _seed()
    CategoriesRepository.create_category(uid, "Tesouro", "investimento")
    cats = {
        c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)
    }

    TransactionsRepository.create_transaction(
        uid, cats["Tesouro"], "2026-05-15", "Aporte", 200.0
    )

    detail = TransactionsRepository.get_dashboard_data(uid, 2026, 5)[
        "descriptions_by_cat"
    ]

    assert detail["Tesouro"]["pct_of_month"] == pytest.approx(100.0)


def test_pct_of_month_no_expenses_no_investments(db_session):
    """Mês sem despesas e sem aportes: pct_of_month é 0.0, sem ZeroDivisionError."""
    uid, cats = _seed()
    CategoriesRepository.create_category(uid, "Tesouro", "investimento")
    cats = {
        c["name"]: c["id"] for c in CategoriesRepository.list_categories(uid)
    }

    # Apenas uma entrada — nenhum lançamento de despesa ou investimento no mês.
    TransactionsRepository.create_transaction(
        uid, cats["Salario"], "2026-05-05", "Pagamento", 1000.0
    )

    detail = TransactionsRepository.get_dashboard_data(uid, 2026, 5)[
        "descriptions_by_cat"
    ]

    assert detail["Mercado"]["pct_of_month"] == pytest.approx(0.0)
    assert detail["Tesouro"]["pct_of_month"] == pytest.approx(0.0)
