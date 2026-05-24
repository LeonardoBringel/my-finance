"""Testes unitários para utils/session.py (JWT de sessão: criação e decodificação)."""

import os
import pathlib
import subprocess
import sys
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


def test_token_signed_with_fernet_key_fails():
    """Token assinado com a antiga FERNET_KEY não é mais aceito (segredo agora é independente)."""
    forged = jwt.encode(
        {"user_id": 1, "exp": datetime.now(timezone.utc) + timedelta(days=1)},
        os.environ["FERNET_KEY"],
        algorithm="HS256",
    )
    assert decode_session_token(forged) is None


def test_missing_jwt_secret_raises():
    """Importar utils.session sem JWT_SECRET definido levanta RuntimeError no import."""
    project_root = str(pathlib.Path(__file__).resolve().parents[2])
    env = {k: v for k, v in os.environ.items() if k != "JWT_SECRET"}
    env["PYTHONPATH"] = os.pathsep.join([project_root, *sys.path])
    # load_dotenv() em session.py busca o .env a partir do diretório do módulo,
    # então o neutralizamos para garantir que JWT_SECRET esteja realmente ausente.
    code = "import dotenv; dotenv.load_dotenv = lambda *a, **k: False; import utils.session"
    proc = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "JWT_SECRET" in proc.stderr
