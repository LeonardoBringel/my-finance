import bcrypt

MIN_PASSWORD_LENGTH = 8


def validate_password(password: str) -> tuple[bool, str]:
    """Valida uma senha contra a política compartilhada (fonte única de verdade).

    Regra atual: comprimento mínimo de MIN_PASSWORD_LENGTH caracteres.

    Args:
        password: Senha em texto plano a validar.

    Returns:
        Tupla (válida, mensagem). Em caso de sucesso a mensagem é vazia; em caso
        de falha, contém um erro em pt-BR pronto para exibição.
    """
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return (
            False,
            f"A senha deve ter ao menos {MIN_PASSWORD_LENGTH} caracteres.",
        )
    return True, ""


def hash_password(plain: str) -> str:
    """Gera um hash bcrypt a partir de uma senha em texto plano."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash bcrypt armazenado."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
