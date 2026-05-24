"""Integration tests for users, categories and cash-flow baseline behavior.

Cobre criação/login de usuários, deduplicação e ownership de categorias e a
população de um mês de fluxo de caixa a partir do template (com clamp de dia).
"""

import pytest

from repositories.cash_flow_month_repository import CashFlowMonthRepository
from repositories.cash_flow_template_repository import (
    CashFlowTemplateRepository,
)
from repositories.categories_repository import CategoriesRepository
from repositories.users_repository import UsersRepository

pytestmark = pytest.mark.integration


def test_first_user_is_admin(db_session):
    """O primeiro usuário criado é admin; os subsequentes não."""
    alice = UsersRepository.create_user("alice", "pw")
    assert alice["is_admin"] is True

    bob = UsersRepository.create_user("bob", "pw")
    assert bob["is_admin"] is False


def test_login_by_username(db_session):
    """login autentica por username e rejeita senha ou usuário inválidos."""
    created = UsersRepository.create_user("alice", "secret")

    ok = UsersRepository.login("alice", "secret")
    assert ok is not None
    assert ok["id"] == created["id"]
    assert ok["username"] == "alice"

    assert UsersRepository.login("alice", "wrong") is None
    assert UsersRepository.login("ghost", "x") is None


def test_category_dedup_and_ownership(db_session):
    """Categorias deduplicam por nome (case-insensitive) e respeitam ownership na exclusão."""
    uid1 = UsersRepository.create_user("alice", "pw")["id"]

    ok, _ = CategoriesRepository.create_category(uid1, "Casa", "saida")
    assert ok is True

    dup_ok, _ = CategoriesRepository.create_category(uid1, "casa", "saida")
    assert dup_ok is False

    cat_id = next(
        c["id"]
        for c in CategoriesRepository.list_categories(uid1)
        if c["name"] == "Casa"
    )

    uid2 = UsersRepository.create_user("bob", "pw")["id"]
    del_ok, _ = CategoriesRepository.delete_category(uid2, cat_id)
    assert del_ok is False

    names = [c["name"] for c in CategoriesRepository.list_categories(uid1)]
    assert "Casa" in names


def test_template_to_month_clamps_day(db_session):
    """create_month copia os itens do template e faz clamp do dia em 28."""
    uid = UsersRepository.create_user("alice", "pw")["id"]

    CashFlowTemplateRepository.save_template(
        uid,
        [
            {"name": "Aluguel", "day": 31, "value": 1500.0, "type": "saida"},
            {"name": "Salario", "day": 5, "value": 4000.0, "type": "entrada"},
        ],
    )

    month = CashFlowMonthRepository.create_month(uid, 2026, 2)
    entries = {e["name"]: e for e in month["entries"]}
    assert len(month["entries"]) == 2

    aluguel = entries["Aluguel"]
    assert aluguel["day"] == 28
    assert aluguel["value"] == pytest.approx(1500.0)
    assert aluguel["type"] == "saida"

    salario = entries["Salario"]
    assert salario["day"] == 5
    assert salario["value"] == pytest.approx(4000.0)
    assert salario["type"] == "entrada"
