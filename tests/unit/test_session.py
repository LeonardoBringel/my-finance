"""Testes unitários para utils/session.py (JWT de sessão: criação e decodificação)."""

from datetime import datetime, timedelta, timezone

import jwt

from utils.session import _SECRET, create_session_token, decode_session_token


def test_token_round_trip():
    """decode_session_token(create_session_token(id)) recupera o user_id original."""
    token = create_session_token(42)
    assert decode_session_token(token) == 42


def test_expired_token_returns_none():
    """Token com exp no passado é considerado inválido e retorna None."""
    expired = jwt.encode(
        {"user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
        _SECRET,
        algorithm="HS256",
    )
    assert decode_session_token(expired) is None


def test_garbage_token_returns_none():
    """String que não é um JWT válido retorna None."""
    assert decode_session_token("not.a.jwt") is None


def test_wrong_secret_token_returns_none():
    """Token assinado com segredo diferente falha na verificação e retorna None."""
    forged = jwt.encode(
        {"user_id": 1, "exp": datetime.now(timezone.utc) + timedelta(days=1)},
        "wrong-secret",
        algorithm="HS256",
    )
    assert decode_session_token(forged) is None
