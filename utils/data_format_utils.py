from datetime import datetime


def format_currency(value: float) -> str:
    """Formata um valor numérico como moeda brasileira (R$ 1.234,56)."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
