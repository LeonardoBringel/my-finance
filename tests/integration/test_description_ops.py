"""Integration tests for bulk description operations on transactions.

Cobre rename_description, delete_description e migrate_description do
TransactionsRepository, validando rowcount, valores descriptografados e a
consistência de description_hash com a descrição armazenada.
"""

import pytest

from models import Transaction
from repositories.categories_repository import CategoriesRepository
from repositories.transactions_repository import TransactionsRepository
from repositories.users_repository import UsersRepository
from utils.crypto import decrypt, hash_for_lookup

pytestmark = pytest.mark.integration


def _seed_user(username="alice"):
    """Cria um usuário e retorna seu id."""
    return UsersRepository.create_user(username, "pw")["id"]


def _make_category(uid, name, type_="saida"):
    """Cria uma categoria e retorna seu id."""
    ok, _ = CategoriesRepository.create_category(uid, name, type_)
    assert ok
    cats = CategoriesRepository.list_categories(uid)
    return next(c["id"] for c in cats if c["name"] == name)


def test_rename_description_updates_rows_and_hash(db_session):
    """rename_description atualiza apenas as linhas correspondentes e mantém o hash consistente."""
    uid = _seed_user()
    cat_id = _make_category(uid, "Mercado", "saida")

    TransactionsRepository.create_transaction(
        uid, cat_id, "2026-05-01", "Padaria", 10.0
    )
    TransactionsRepository.create_transaction(
        uid, cat_id, "2026-05-02", "Padaria", 20.0
    )
    TransactionsRepository.create_transaction(
        uid, cat_id, "2026-05-03", "Farmacia", 30.0
    )

    count = TransactionsRepository.rename_description(uid, cat_id, "Padaria", "Pão")
    assert count == 2

    txns = TransactionsRepository.list_transactions(uid)
    descriptions = [t["description"] for t in txns]
    assert descriptions.count("Pão") == 2
    assert descriptions.count("Padaria") == 0
    assert descriptions.count("Farmacia") == 1

    rows = db_session.query(Transaction).filter_by(user_id=uid).all()
    renamed = [r for r in rows if r.description and decrypt(r.description) == "Pão"]
    assert len(renamed) == 2
    for row in renamed:
        assert row.description_hash == hash_for_lookup("Pão")
        assert row.description_hash == hash_for_lookup(decrypt(row.description))


def test_delete_description_nulls_rows(db_session):
    """delete_description zera description e description_hash das linhas correspondentes."""
    uid = _seed_user()
    cat_id = _make_category(uid, "Transporte", "saida")

    TransactionsRepository.create_transaction(uid, cat_id, "2026-05-01", "Uber", 15.0)
    TransactionsRepository.create_transaction(uid, cat_id, "2026-05-02", "Uber", 25.0)

    count = TransactionsRepository.delete_description(uid, cat_id, "Uber")
    assert count == 2

    rows = db_session.query(Transaction).filter_by(user_id=uid).all()
    assert len(rows) == 2
    for row in rows:
        assert row.description is None
        assert row.description_hash is None


def test_migrate_description_moves_category_and_desc(db_session):
    """migrate_description move categoria e descrição mantendo o hash coerente."""
    uid = _seed_user()
    a_id = _make_category(uid, "A", "saida")
    b_id = _make_category(uid, "B", "saida")

    TransactionsRepository.create_transaction(uid, a_id, "2026-05-01", "X", 5.0)
    TransactionsRepository.create_transaction(uid, a_id, "2026-05-02", "X", 7.0)

    count = TransactionsRepository.migrate_description(uid, a_id, "X", b_id, "Y")
    assert count == 2

    rows = db_session.query(Transaction).filter_by(user_id=uid).all()
    assert len(rows) == 2
    for row in rows:
        assert row.category_id == b_id
        assert decrypt(row.description) == "Y"
        assert row.description_hash == hash_for_lookup("Y")
