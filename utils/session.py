import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

load_dotenv()

_SECRET = os.getenv("FERNET_KEY", "missing-secret")
_ALGORITHM = "HS256"

COOKIE_NAME = "finance_session"
TOKEN_EXPIRY_DAYS = 30


def create_session_token(user_id: int) -> str:
    """Gera um JWT assinado contendo o user_id com expiração de TOKEN_EXPIRY_DAYS dias.

    Args:
        user_id: ID do usuário autenticado.

    Returns:
        Token JWT como string.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def decode_session_token(token: str) -> int | None:
    """Decodifica e valida um JWT de sessão.

    Args:
        token: Token JWT a validar.

    Returns:
        user_id contido no token, ou None se inválido/expirado.
    """
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
        return payload.get("user_id")
    except jwt.PyJWTError:
        return None
