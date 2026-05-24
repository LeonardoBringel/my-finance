"""Testes unitários para utils/password_utils.py (hash, verificação bcrypt e política)."""

from utils.password_utils import (
    MIN_PASSWORD_LENGTH,
    hash_password,
    validate_password,
    verify_password,
)


def test_hash_verify_round_trip():
    """verify_password aceita o hash gerado por hash_password para a mesma senha."""
    senha = "s3nh4-F0rt3!"
    hashed = hash_password(senha)
    assert hashed != senha  # o hash não é o texto puro
    assert verify_password(senha, hashed) is True


def test_verify_wrong_password_returns_false():
    """verify_password retorna False quando a senha não corresponde ao hash."""
    assert verify_password("wrong", hash_password("correct")) is False


def test_hash_same_password_yields_different_hashes():
    """Hashes da mesma senha diferem (salt aleatório), mas ambos verificam True."""
    senha = "repeat-me"
    h1 = hash_password(senha)
    h2 = hash_password(senha)
    assert h1 != h2
    assert verify_password(senha, h1) is True
    assert verify_password(senha, h2) is True


def test_validate_password_rejects_below_minimum():
    """Senha com 7 caracteres (abaixo do mínimo de 8) é rejeitada com mensagem pt-BR."""
    ok, msg = validate_password("a" * (MIN_PASSWORD_LENGTH - 1))
    assert ok is False
    assert str(MIN_PASSWORD_LENGTH) in msg
    assert msg  # mensagem de erro não vazia


def test_validate_password_accepts_exact_minimum():
    """Senha com exatamente 8 caracteres (limite) é aceita (>=, não >)."""
    ok, msg = validate_password("a" * MIN_PASSWORD_LENGTH)
    assert ok is True
    assert msg == ""


def test_validate_password_accepts_longer():
    """Senha acima do mínimo é aceita."""
    ok, _ = validate_password("a" * (MIN_PASSWORD_LENGTH + 5))
    assert ok is True


def test_validate_password_rejects_empty():
    """Senha vazia ou None é rejeitada."""
    assert validate_password("")[0] is False
    assert validate_password(None)[0] is False
