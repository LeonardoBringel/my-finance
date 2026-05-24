"""Testes unitários para utils/crypto.py (Fernet, HMAC lookup, parsing numérico)."""

from utils import crypto


def test_encrypt_decrypt_round_trip():
    """decrypt(encrypt(s)) recupera a string original, incluindo acentos."""
    for original in ("hello world", "Mercadão", "café com leite çãõ"):
        token = crypto.encrypt(original)
        assert token != original  # foi de fato cifrado
        assert crypto.decrypt(token) == original


def test_encrypt_none_and_empty_return_empty_string():
    """encrypt(None) e encrypt('') retornam string vazia."""
    assert crypto.encrypt(None) == ""
    assert crypto.encrypt("") == ""


def test_decrypt_empty_and_none_return_none():
    """decrypt('') e decrypt(None) retornam None."""
    assert crypto.decrypt("") is None
    assert crypto.decrypt(None) is None


def test_decrypt_invalid_token_returns_unchanged():
    """Token inválido (não-Fernet) é retornado sem alteração (plaintext legado)."""
    assert crypto.decrypt("not-a-valid-token") == "not-a-valid-token"


def test_hash_for_lookup_deterministic_and_collision_free():
    """hash_for_lookup é determinístico, distingue entradas e retorna '' para vazio."""
    assert crypto.hash_for_lookup("x") == crypto.hash_for_lookup("x")
    assert crypto.hash_for_lookup("x") != crypto.hash_for_lookup("y")
    assert crypto.hash_for_lookup("") == ""


def test_decrypt_float_round_trip_and_fallbacks():
    """decrypt_float decifra números e retorna 0.0 em entradas inválidas."""
    assert crypto.decrypt_float(crypto.encrypt("12.5")) == 12.5
    assert crypto.decrypt_float(None) == 0.0
    assert crypto.decrypt_float("not-a-number") == 0.0
