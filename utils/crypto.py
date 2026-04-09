import hashlib
import hmac as _hmac_mod
import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

_key = os.getenv("FERNET_KEY")
if not _key:
    raise RuntimeError("FERNET_KEY not set in environment. Check your .env file.")

_fernet = Fernet(_key.encode() if isinstance(_key, str) else _key)


def encrypt(value) -> str:
    """Criptografa qualquer valor para string. Retorna string vazia para None/empty."""
    if value is None:
        return ""
    text = str(value)
    if not text:
        return ""
    return _fernet.encrypt(text.encode()).decode()


def decrypt(token: str):
    """Descriptografa um token de volta para string. Retorna None para None/empty."""
    if not token:
        return None
    try:
        return _fernet.decrypt(token.encode()).decode()
    except Exception:
        # Dado legado em texto plano — retorna como está
        return token


def hash_for_lookup(value: str) -> str:
    """Gera um HMAC-SHA256 determinístico para lookups indexados no banco de dados.

    Usa a FERNET_KEY como segredo do HMAC, vinculando o hash a esta instalação.

    Args:
        value: Valor em texto plano a ser hasheado.

    Returns:
        Digest hexadecimal HMAC-SHA256, ou string vazia para entrada vazia.
    """
    if not value:
        return ""
    return _hmac_mod.new(
        _key.encode(),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def decrypt_float(token: str) -> float:
    """Descriptografa um token e converte para float."""
    val = decrypt(token)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0
