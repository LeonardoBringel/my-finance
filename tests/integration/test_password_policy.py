"""Integration tests for the shared password policy at the repository layer.

Garante que senhas abaixo da política (mínimo de 8 caracteres) são rejeitadas em
todos os caminhos de escrita (criação e troca de senha) e que nada é persistido.
"""

import pytest

from models import User
from repositories.users_repository import UsersRepository

pytestmark = pytest.mark.integration


def test_create_user_rejects_weak_password(db_session):
    """create_user levanta ValueError para senha curta e não persiste o usuário."""
    with pytest.raises(ValueError):
        UsersRepository.create_user("alice", "short")  # 5 caracteres

    assert db_session.query(User).count() == 0


def test_create_user_accepts_policy_compliant_password(db_session):
    """create_user persiste normalmente quando a senha atende à política."""
    user = UsersRepository.create_user("alice", "password")  # 8 caracteres
    assert user["id"] is not None
    assert db_session.query(User).count() == 1


def test_update_password_rejects_weak_password(db_session):
    """update_user_password rejeita senha curta sem alterar o hash."""
    uid = UsersRepository.create_user("alice", "password")["id"]

    ok, msg = UsersRepository.update_user_password(uid, "password", "weak")
    assert ok is False
    assert msg

    # A senha antiga ainda autentica — nada foi alterado.
    assert UsersRepository.login("alice", "password") is not None


def test_admin_reset_rejects_weak_password(db_session):
    """admin_update_user_password rejeita senha curta (reset por admin)."""
    uid = UsersRepository.create_user("alice", "password")["id"]

    ok, msg = UsersRepository.admin_update_user_password(uid, "weak")
    assert ok is False
    assert msg

    assert UsersRepository.login("alice", "password") is not None
