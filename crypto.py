import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

_key = os.getenv("FERNET_KEY")
if not _key:
    raise RuntimeError("FERNET_KEY not set in environment. Check your .env file.")

_fernet = Fernet(_key.encode() if isinstance(_key, str) else _key)


# ── Password hashing ───────────────────────────────────────────────────────────
def encrypt(value) -> str:
    """Encrypt any value to a string. Returns empty string for None/empty."""
    if value is None:
        return ""
    text = str(value)
    if not text:
        return ""
    return _fernet.encrypt(text.encode()).decode()


def decrypt(token: str):
    """Decrypt a token back to string. Returns None for None/empty."""
    if not token:
        return None
    try:
        return _fernet.decrypt(token.encode()).decode()
    except Exception:
        # Already plain text (e.g. legacy data) — return as-is
        return token


def decrypt_float(token: str) -> float:
    """Decrypt and convert to float."""
    val = decrypt(token)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0
