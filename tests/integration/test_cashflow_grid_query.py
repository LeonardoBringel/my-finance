"""Testes de integração para CashFlowMonthRepository.list_months_with_entries.

Cobrem PERF-02: a grade anual do fluxo de caixa é carregada com um número
constante de consultas (sem N+1), trazendo todos os meses + lançamentos do ano
descriptografados, no mesmo formato de get_month_with_entries.
"""

import pytest
from sqlalchemy import event

from repositories.cash_flow_entry_repository import CashFlowEntryRepository
from repositories.cash_flow_month_repository import CashFlowMonthRepository
from repositories.users_repository import UsersRepository

pytestmark = pytest.mark.integration


def _seed_user(username="alice"):
    """Cria um usuário e retorna seu id."""
    return UsersRepository.create_user(username, "password")["id"]


def _count_cashflow_selects(engine, fn):
    """Executa fn() contando os SELECTs emitidos nas tabelas de fluxo de caixa."""
    counter = {"n": 0}

    def before(conn, cursor, statement, parameters, context, executemany):
        s = statement.lstrip().upper()
        if s.startswith("SELECT") and "CASH_FLOW" in statement.upper():
            counter["n"] += 1

    event.listen(engine, "before_cursor_execute", before)
    try:
        result = fn()
    finally:
        event.remove(engine, "before_cursor_execute", before)
    return result, counter["n"]


def test_single_query_returns_all_months_with_entries(db_session, pg_engine):
    """12 meses com lançamentos retornam em consultas constantes (sem N+1)."""
    uid = _seed_user()
    for m in range(1, 13):
        month = CashFlowMonthRepository.create_month(uid, 2026, m)
        CashFlowEntryRepository.add_entry(
            month["id"], "Salario", 5, 4000.0, "entrada"
        )
        CashFlowEntryRepository.add_entry(
            month["id"], "Aluguel", 10, 1500.0, "saida"
        )

    months, n_queries = _count_cashflow_selects(
        pg_engine,
        lambda: CashFlowMonthRepository.list_months_with_entries(uid, 2026),
    )

    assert len(months) == 12
    # selectinload => 2 consultas (meses + lançamentos via IN), constante para
    # qualquer quantidade de meses. O laço antigo faria 12+ round-trips.
    assert n_queries <= 2

    for month in months:
        names = {e["name"] for e in month["entries"]}
        assert names == {"Salario", "Aluguel"}
        for e in month["entries"]:
            if e["name"] == "Salario":
                assert e["value"] == pytest.approx(4000.0)
                assert e["type"] == "entrada"
            else:
                assert e["value"] == pytest.approx(1500.0)
                assert e["type"] == "saida"


def test_shape_matches_get_month_with_entries(db_session):
    """Cada mês retornado tem o mesmo formato/decriptação de get_month_with_entries."""
    uid = _seed_user()
    month = CashFlowMonthRepository.create_month(uid, 2026, 7)
    CashFlowEntryRepository.add_entry(month["id"], "Luz", 8, 200.0, "saida")
    CashFlowEntryRepository.add_entry(month["id"], "Bonus", 1, 900.0, "entrada")

    from_list = {
        m["month"]: m
        for m in CashFlowMonthRepository.list_months_with_entries(uid, 2026)
    }
    single = CashFlowMonthRepository.get_month_with_entries(uid, 2026, 7)

    assert from_list[7] == single


def test_empty_year_returns_empty_list(db_session):
    """Ano sem meses retorna lista vazia, sem erro (edge case)."""
    uid = _seed_user()

    assert CashFlowMonthRepository.list_months_with_entries(uid, 2030) == []
