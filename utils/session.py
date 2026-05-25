import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

load_dotenv()

_SECRET = os.getenv("JWT_SECRET")
if not _SECRET:
    raise RuntimeError(
        "JWT_SECRET not set in environment. Check your .env file."
    )

_ALGORITHM = "HS256"

COOKIE_NAME = "finance_session"
TOKEN_EXPIRY_DAYS = 30


def create_session_token(user_id: int, token_version: int) -> str:
    """Gera um JWT assinado contendo o user_id e o token_version, com expiração de
    TOKEN_EXPIRY_DAYS dias.

    Args:
        user_id: ID do usuário autenticado.
        token_version: Versão de sessão atual do usuário (usada para revogação).

    Returns:
        Token JWT como string.
    """
    payload = {
        "user_id": user_id,
        "token_version": token_version,
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def decode_session_token(token: str) -> dict | None:
    """Decodifica e valida um JWT de sessão.

    Args:
        token: Token JWT a validar.

    Returns:
        Dict com 'user_id' e 'token_version' (este último None quando o claim
        está ausente, ex.: tokens antigos), ou None se inválido/expirado.
    """
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
        return {
            "user_id": payload.get("user_id"),
            "token_version": payload.get("token_version"),
        }
    except jwt.PyJWTError:
        return None
