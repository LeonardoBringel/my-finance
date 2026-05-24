"""Integration tests for cash-flow field encryption at rest.

Validam que name/value de cash_flow_entries e cash_flow_template_items são
persistidos como ciphertext Fernet, enquanto os repositórios retornam os
valores originais descriptografados, e que a cópia template→mês re-encripta
os itens copiados.
"""

import pytest

from models import CashFlowEntry, CashFlowTemplateItem
from repositories.cash_flow_entry_repository import CashFlowEntryRepository
from repositories.cash_flow_month_repository import CashFlowMonthRepository
from repositories.cash_flow_template_repository import (
    CashFlowTemplateRepository,
)
from repositories.users_repository import UsersRepository
from utils.crypto import decrypt, decrypt_float

pytestmark = pytest.mark.integration


def _seed_user(username="alice"):
    """Cria um usuário e retorna seu id."""
    return UsersRepository.create_user(username, "password")["id"]


def test_add_entry_stores_ciphertext_and_reads_plaintext(db_session):
    """add_entry persiste name/value como ciphertext; a leitura retorna os originais."""
    uid = _seed_user()
    month = CashFlowMonthRepository.create_month(uid, 2026, 3)

    CashFlowEntryRepository.add_entry(month["id"], "Aluguel", 10, 1500.0, "saida")

    row = db_session.query(CashFlowEntry).filter_by(month_id=month["id"]).one()
    assert row.name != "Aluguel"
    assert row.value != "1500.0"
    assert decrypt(row.name) == "Aluguel"
    assert decrypt_float(row.value) == pytest.approx(1500.0)

    fresh = CashFlowMonthRepository.get_month_with_entries(uid, 2026, 3)
    entry = fresh["entries"][0]
    assert entry["name"] == "Aluguel"
    assert entry["value"] == pytest.approx(1500.0)
    assert entry["day"] == 10
    assert entry["type"] == "saida"


def test_update_entry_round_trips(db_session):
    """update_entry re-encripta name/value e a leitura retorna os novos valores."""
    uid = _seed_user()
    month = CashFlowMonthRepository.create_month(uid, 2026, 4)
    CashFlowEntryRepository.add_entry(month["id"], "Luz", 5, 200.0, "saida")

    row = db_session.query(CashFlowEntry).filter_by(month_id=month["id"]).one()
    entry_id = row.id
    CashFlowEntryRepository.update_entry(entry_id, "Energia", 6, 250.5, "saida")

    db_session.expire_all()
    updated = db_session.query(CashFlowEntry).filter_by(id=entry_id).one()
    assert updated.name != "Energia"
    assert decrypt(updated.name) == "Energia"
    assert decrypt_float(updated.value) == pytest.approx(250.5)

    fresh = CashFlowMonthRepository.get_month_with_entries(uid, 2026, 4)
    entry = fresh["entries"][0]
    assert entry["name"] == "Energia"
    assert entry["value"] == pytest.approx(250.5)
    assert entry["day"] == 6


def test_save_template_stores_ciphertext_and_get_template_decrypts(db_session):
    """save_template persiste ciphertext; get_template retorna os valores originais."""
    uid = _seed_user()
    CashFlowTemplateRepository.save_template(
        uid,
        [
            {"name": "Salario", "day": 5, "value": 4000.0, "type": "entrada"},
            {"name": "Aluguel", "day": 31, "value": 1500.0, "type": "saida"},
        ],
    )

    rows = db_session.query(CashFlowTemplateItem).all()
    assert len(rows) == 2
    for r in rows:
        assert r.name not in ("Salario", "Aluguel")
        assert decrypt(r.name) in ("Salario", "Aluguel")

    tmpl = CashFlowTemplateRepository.get_template(uid)
    items = {i["name"]: i for i in tmpl["items"]}
    assert items["Salario"]["value"] == pytest.approx(4000.0)
    assert items["Salario"]["type"] == "entrada"
    assert items["Aluguel"]["value"] == pytest.approx(1500.0)
    assert items["Aluguel"]["day"] == 31


def test_template_to_month_copy_encrypts_and_round_trips(db_session):
    """create_month copia itens do template como ciphertext, com clamp de dia e round-trip."""
    uid = _seed_user()
    CashFlowTemplateRepository.save_template(
        uid,
        [
            {"name": "Aluguel", "day": 31, "value": 1500.0, "type": "saida"},
            {"name": "Salario", "day": 5, "value": 4000.0, "type": "entrada"},
        ],
    )

    month = CashFlowMonthRepository.create_month(uid, 2026, 5)

    rows = db_session.query(CashFlowEntry).filter_by(month_id=month["id"]).all()
    assert len(rows) == 2
    for r in rows:
        assert r.name not in ("Aluguel", "Salario")
        assert decrypt(r.name) in ("Aluguel", "Salario")

    entries = {e["name"]: e for e in month["entries"]}
    assert entries["Aluguel"]["value"] == pytest.approx(1500.0)
    assert entries["Aluguel"]["day"] == 28  # clamped
    assert entries["Salario"]["value"] == pytest.approx(4000.0)
    assert entries["Salario"]["day"] == 5


def test_zero_value_round_trips(db_session):
    """value 0 faz round-trip para 0.0 sem erro."""
    uid = _seed_user()
    month = CashFlowMonthRepository.create_month(uid, 2026, 6)
    CashFlowEntryRepository.add_entry(month["id"], "Reserva", 1, 0.0, "entrada")

    fresh = CashFlowMonthRepository.get_month_with_entries(uid, 2026, 6)
    assert fresh["entries"][0]["value"] == pytest.approx(0.0)
