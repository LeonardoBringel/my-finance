from datetime import datetime

from utils.i18n import t

# Ordenados de Janeiro a Dezembro: os call sites indexam por `mes - 1`.
MONTH_NAMES = t("months.full")


def format_value_brl(value: float) -> str:
    """Formata um valor numérico no padrão brasileiro, sem prefixo de moeda (1.234,56)."""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_currency(value: float) -> str:
    """Formata um valor numérico como moeda brasileira (R$ 1.234,56)."""
    return f"R$ {format_value_brl(value)}"


def mask_value_input(raw: str) -> str:
    """Aplica máscara monetária progressiva sobre texto digitado.

    Extrai apenas os dígitos de `raw` e os interpreta como centavos, formatando
    o resultado no padrão brasileiro. Retorna string vazia se não houver dígitos.
    """
    digits = "".join(filter(str.isdigit, raw))
    if not digits:
        return ""
    return format_value_brl(int(digits) / 100)


def format_date(date: str) -> str:
    """Converte uma data no formato ISO (YYYY-MM-DD) para o formato brasileiro (DD/MM/YYYY)."""
    try:
        return datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return date


def parse_value_text(value: str) -> float | None:
    """Converte uma string de valor monetário no formato brasileiro para float.

    Aceita formatos como '1.250,00' ou '1250.00'.
    Retorna None se o valor não puder ser interpretado.
    """
    value = value.strip().replace(" ", "")
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None
