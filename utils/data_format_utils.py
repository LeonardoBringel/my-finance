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
    """Reformata texto digitado como um valor monetário no padrão brasileiro.

    A vírgula é o separador decimal: dígitos antes dela formam a parte inteira
    (reais) e até dois dígitos depois dela formam os centavos (completados com
    zero à direita se faltar um dígito, truncados se sobrar). Sem vírgula, todo
    o texto é interpretado como reais inteiros (`"100"` → `"100,00"`). Qualquer
    caractere que não seja dígito é ignorado. Retorna string vazia se não houver
    nenhum dígito.
    """
    integer_part, _, decimal_part = raw.partition(",")
    integer_digits = "".join(filter(str.isdigit, integer_part))
    decimal_digits = "".join(filter(str.isdigit, decimal_part))
    if not integer_digits and not decimal_digits:
        return ""
    cents = decimal_digits[:2].ljust(2, "0")
    value = int(integer_digits or "0") + int(cents) / 100
    return format_value_brl(value)


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
