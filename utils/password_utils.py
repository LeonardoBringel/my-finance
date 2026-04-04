import bcrypt


def hash_password(plain: str) -> str:
    """Gera um hash bcrypt a partir de uma senha em texto plano."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash bcrypt armazenado."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
