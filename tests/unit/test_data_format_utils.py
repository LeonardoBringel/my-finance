"""Testes unitários para utils/data_format_utils.py (moeda, data, parsing de valores)."""

from utils.data_format_utils import (
    format_currency,
    format_date,
    parse_value_text,
)


def test_format_currency_brl():
    """Formata float no padrão BR com ponto de milhar e vírgula decimal."""
    assert format_currency(1234.5) == "R$ 1.234,50"


def test_format_currency_small_value():
    """Valores abaixo de mil não recebem separador de milhar."""
    assert format_currency(5.0) == "R$ 5,00"


def test_format_currency_millions():
    """Valores na casa dos milhões recebem dois separadores de milhar."""
    assert format_currency(1234567.89) == "R$ 1.234.567,89"


def test_format_date_iso_to_br():
    """Converte data ISO YYYY-MM-DD para o formato BR DD/MM/YYYY."""
    assert format_date("2026-05-23") == "23/05/2026"


def test_format_date_invalid_passthrough():
    """Entrada não parseável é retornada sem alteração."""
    assert format_date("not-a-date") == "not-a-date"


def test_parse_value_text_br_format():
    """String no padrão BR: pontos são milhar e vírgula é decimal."""
    assert parse_value_text("1.250,00") == 1250.0


def test_parse_value_text_plain_format():
    """String sem vírgula é interpretada como float direto."""
    assert parse_value_text("1250.00") == 1250.0


def test_parse_value_text_invalid_returns_none():
    """Entrada não numérica retorna None."""
    assert parse_value_text("abc") is None
