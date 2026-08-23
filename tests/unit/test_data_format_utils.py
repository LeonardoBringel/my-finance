"""Testes unitários para utils/data_format_utils.py (moeda, data, parsing de valores)."""

from datetime import date

from utils.data_format_utils import (
    MONTH_NAMES,
    days_in_period,
    format_currency,
    format_date,
    format_value_brl,
    mask_value_input,
    parse_value_text,
)


def test_month_names_suporta_os_call_sites():
    """Os call sites indexam por `mes - 1`, buscam por `.index()` e fatiam `[:3]`."""
    assert len(MONTH_NAMES) == 12
    assert MONTH_NAMES[0] == "Janeiro"
    assert MONTH_NAMES[11] == "Dezembro"
    assert MONTH_NAMES.index("Março") + 1 == 3
    assert [m[:3] for m in MONTH_NAMES[:3]] == ["Jan", "Fev", "Mar"]


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


def test_format_value_brl_thousands():
    """Formata sem prefixo R$, com ponto de milhar e vírgula decimal."""
    assert format_value_brl(13716.36) == "13.716,36"


def test_format_value_brl_zero():
    """Zero formata como '0,00'."""
    assert format_value_brl(0.0) == "0,00"


def test_format_value_brl_below_one():
    """Valores abaixo de um real mantêm as duas casas decimais."""
    assert format_value_brl(0.5) == "0,50"


def test_format_currency_uses_format_value_brl():
    """format_currency permanece idêntica após a extração do helper."""
    assert format_currency(89.0) == "R$ 89,00"


def test_mask_value_input_plain_digits_are_whole_reais():
    """Sem vírgula, o texto digitado é a parte inteira em reais, não centavos."""
    assert mask_value_input("1") == "1,00"
    assert mask_value_input("10") == "10,00"
    assert mask_value_input("100") == "100,00"
    assert mask_value_input("137163") == "137.163,00"


def test_mask_value_input_comma_is_decimal_separator():
    """A vírgula separa reais de centavos; um dígito decimal completa com zero."""
    assert mask_value_input("0,5") == "0,50"
    assert mask_value_input("12,3") == "12,30"
    assert mask_value_input("1.371,63") == "1.371,63"


def test_mask_value_input_truncates_extra_decimal_digits():
    """Mais de dois dígitos decimais são truncados, não arredondados."""
    assert mask_value_input("12,345") == "12,34"


def test_mask_value_input_empty_without_digits():
    """String sem nenhum dígito vira vazia."""
    assert mask_value_input("abc") == ""
    assert mask_value_input("") == ""


def test_mask_value_input_idempotent_on_own_output():
    """Reaplicar a máscara sobre a própria saída não muda o valor."""
    once = mask_value_input("137163")
    assert mask_value_input(once) == once


def test_days_in_period_current_month_first_day():
    """Mês corrente no dia 1: denominador é 1, nunca 0."""
    assert days_in_period(2025, 1, today=date(2025, 1, 1)) == 1


def test_days_in_period_current_month_mid_month():
    """Mês corrente: dias decorridos até hoje, inclusive."""
    assert days_in_period(2025, 1, today=date(2025, 1, 9)) == 9


def test_days_in_period_closed_month():
    """Mês fechado: total de dias do mês."""
    assert days_in_period(2025, 1, today=date(2025, 2, 15)) == 31


def test_days_in_period_future_month():
    """Mês futuro: total de dias do mês, não dias decorridos."""
    assert days_in_period(2026, 12, today=date(2026, 8, 23)) == 31


def test_days_in_period_leap_february():
    """Fevereiro de ano bissexto: 29 dias quando o mês já fechou."""
    assert days_in_period(2024, 2, today=date(2024, 3, 1)) == 29


def test_days_in_period_non_leap_february():
    """Fevereiro de ano não-bissexto: 28 dias quando o mês já fechou."""
    assert days_in_period(2025, 2, today=date(2025, 3, 1)) == 28
