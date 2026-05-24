"""Testes unitários para utils/password_utils.py (hash e verificação bcrypt)."""

from utils.password_utils import hash_password, verify_password


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
