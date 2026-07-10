"""Fonte única da verdade dos tipos de categoria/transação.

O tipo de uma transação não é persistido: ele é derivado do tipo da sua categoria
(ver `TransactionsRepository.list_transactions`). Comparar tipos por string literal
espalhada pelo código faz um tipo novo escapar silenciosamente de alguma agregação —
todas as comparações devem passar pelos helpers deste módulo.
"""

INCOME = "entrada"
EXPENSE = "saida"
BOTH = "ambos"
INVESTMENT = "investimento"

# Tipos de categoria cujos lançamentos debitam o usuário (contam como despesa).
EXPENSE_TYPES = (EXPENSE, BOTH)

# Todos os tipos que uma categoria pode ter, em ordem canônica para seletores.
ALL_TYPES = (EXPENSE, INCOME, INVESTMENT, BOTH)

# Tipos escolhíveis ao lançar uma transação ('ambos' é só uma marcação de categoria).
TRANSACTION_TYPES = (EXPENSE, INCOME, INVESTMENT)

TYPE_LABELS = {
    EXPENSE: "💸 Saída",
    INCOME: "💰 Entrada",
    INVESTMENT: "📈 Investimento",
    BOTH: "🔄 Ambos",
}


def is_expense(type_: str) -> bool:
    """Retorna True se o tipo conta como despesa ('saida' ou 'ambos')."""
    return type_ in EXPENSE_TYPES


def is_income(type_: str) -> bool:
    """Retorna True se o tipo é entrada."""
    return type_ == INCOME


def is_investment(type_: str) -> bool:
    """Retorna True se o tipo é investimento."""
    return type_ == INVESTMENT


def categories_for(type_: str) -> tuple[str, ...]:
    """Tipos de categoria elegíveis para um lançamento do tipo informado.

    Args:
        type_: Tipo do lançamento ('saida', 'entrada' ou 'investimento').

    Returns:
        Tupla de tipos de categoria aceitos. Investimento nunca aceita 'ambos',
        pois uma categoria 'ambos' representa entrada ou saída.
    """
    if type_ == INVESTMENT:
        return (INVESTMENT,)
    if type_ in (EXPENSE, INCOME):
        return (type_, BOTH)
    return ()


def selectable_type(type_: str) -> str:
    """Converte um tipo de categoria no tipo de lançamento correspondente.

    Uma transação de categoria 'ambos' não tem tipo próprio de lançamento; ela é
    apresentada como saída. Usado para posicionar seletores de tipo na UI sem
    estourar em tipos ausentes da lista de opções.
    """
    return type_ if type_ in TRANSACTION_TYPES else EXPENSE
