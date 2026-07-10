"""Fonte única da verdade dos tipos de categoria/transação.

O tipo de uma transação não é persistido: ele é derivado do tipo da sua categoria
(ver `TransactionsRepository.list_transactions`). Comparar tipos por string literal
espalhada pelo código faz um tipo novo escapar silenciosamente de alguma agregação —
todas as comparações devem passar pelos helpers deste módulo.

As constantes abaixo são **valores persistidos** (criptografados) em
`categories.type`, não texto de interface: renomeá-las corrompe dados existentes.
Só os rótulos de exibição (`TYPE_LABELS`) vêm do mapping de i18n.
"""

from utils.i18n import t

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

# Rótulos de exibição, chaveados pelo valor persistido. Construído a partir de
# ALL_TYPES para que um tipo novo sem rótulo estoure no import, não na tela.
TYPE_LABELS = {type_: t(f"domain.category_type.{type_}") for type_ in ALL_TYPES}


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


def migration_targets(source_type: str) -> tuple[str, ...]:
    """Tipos de categoria válidos como destino ao migrar uma descrição.

    A regra é a direção do dinheiro: o que sai da conta pode ser gasto ou
    investido, então esses tipos migram entre si (é o que permite reclassificar
    um aporte lançado como despesa). O que entra fica isolado, para que uma
    despesa não vire entrada por acidente e inverta o sinal do saldo.

    Args:
        source_type: Tipo da categoria de origem.

    Returns:
        Tupla de tipos de categoria aceitos como destino.
    """
    if is_income(source_type):
        return (INCOME, BOTH)
    return (EXPENSE, BOTH, INVESTMENT)


def selectable_type(type_: str) -> str:
    """Converte um tipo de categoria no tipo de lançamento correspondente.

    Uma transação de categoria 'ambos' não tem tipo próprio de lançamento; ela é
    apresentada como saída. Usado para posicionar seletores de tipo na UI sem
    estourar em tipos ausentes da lista de opções.
    """
    return type_ if type_ in TRANSACTION_TYPES else EXPENSE
