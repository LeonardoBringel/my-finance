"""Integration tests for session revocation via per-user token_version.

Verifica que: novos usuários começam em token_version 0; o token embute essa
versão; trocar a senha (própria ou via admin) incrementa a versão, de modo que
um token antigo deixa de coincidir com a versão atual (e seria rejeitado por
require_login).
"""

import pytest

from repositories.users_repository import UsersRepository
from utils.session import create_session_token, decode_session_token

pytestmark = pytest.mark.integration


def test_new_user_starts_at_version_zero(db_session):
    """Usuário recém-criado tem token_version 0 (server_default)."""
    UsersRepository.create_user("alice", "password")
    user = UsersRepository.login("alice", "password")
    assert user["token_version"] == 0


def test_password_change_revokes_old_token(db_session):
    """Trocar a própria senha incrementa token_version; o token antigo não coincide mais."""
    uid = UsersRepository.create_user("alice", "password")["id"]
    tv0 = UsersRepository.get_user_by_id(uid)["token_version"]

    # Token emitido com a versão atual (mecanismo do login()).
    old_token = create_session_token(uid, tv0)
    assert decode_session_token(old_token)["token_version"] == tv0

    ok, _ = UsersRepository.update_user_password(uid, "password", "password-new")
    assert ok is True

    current = UsersRepository.get_user_by_id(uid)["token_version"]
    assert current == tv0 + 1
    # A versão embutida no token antigo difere da versão atual -> rejeitado.
    assert decode_session_token(old_token)["token_version"] != current


def test_admin_reset_revokes_old_token(db_session):
    """Reset de senha por admin também incrementa token_version."""
    uid = UsersRepository.create_user("alice", "password")["id"]
    tv0 = UsersRepository.get_user_by_id(uid)["token_version"]
    old_token = create_session_token(uid, tv0)

    ok, _ = UsersRepository.admin_update_user_password(uid, "password-reset")
    assert ok is True

    current = UsersRepository.get_user_by_id(uid)["token_version"]
    assert current == tv0 + 1
    assert decode_session_token(old_token)["token_version"] != current
