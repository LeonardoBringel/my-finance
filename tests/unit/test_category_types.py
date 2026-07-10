from utils.category_types import (
    ALL_TYPES,
    BOTH,
    EXPENSE,
    INCOME,
    INVESTMENT,
    TRANSACTION_TYPES,
    TYPE_LABELS,
    categories_for,
    is_expense,
    is_income,
    is_investment,
    selectable_type,
)


def test_is_expense_cobre_saida_e_ambos():
    """Despesa abrange 'saida' e 'ambos'; nunca entrada ou investimento."""
    assert is_expense(EXPENSE)
    assert is_expense(BOTH)
    assert not is_expense(INCOME)
    assert not is_expense(INVESTMENT)


def test_is_income_e_is_investment_sao_exclusivos():
    """Entrada e investimento são tipos distintos e não se sobrepõem."""
    assert is_income(INCOME)
    assert not is_income(INVESTMENT)
    assert is_investment(INVESTMENT)
    assert not is_investment(INCOME)
    assert not is_investment(EXPENSE)


def test_investimento_nunca_aceita_categoria_ambos():
    """Um lançamento de investimento só aceita categorias de investimento."""
    assert categories_for(INVESTMENT) == (INVESTMENT,)
    assert BOTH not in categories_for(INVESTMENT)


def test_categories_for_saida_e_entrada_incluem_ambos():
    """Saída e entrada aceitam também categorias marcadas como 'ambos'."""
    assert set(categories_for(EXPENSE)) == {EXPENSE, BOTH}
    assert set(categories_for(INCOME)) == {INCOME, BOTH}


def test_categories_for_tipo_desconhecido_retorna_vazio():
    """Tipo desconhecido não habilita nenhuma categoria."""
    assert categories_for(BOTH) == ()
    assert categories_for("inexistente") == ()


def test_selectable_type_mapeia_ambos_para_saida():
    """'ambos' não é um tipo de lançamento; cai em saída sem estourar."""
    assert selectable_type(BOTH) == EXPENSE
    assert selectable_type("inexistente") == EXPENSE
    for type_ in TRANSACTION_TYPES:
        assert selectable_type(type_) == type_


def test_todos_os_tipos_tem_label():
    """Todo tipo de categoria tem rótulo de UI e ordem canônica estável."""
    assert set(ALL_TYPES) == set(TYPE_LABELS)
    assert ALL_TYPES == (EXPENSE, INCOME, INVESTMENT, BOTH)
    assert BOTH not in TRANSACTION_TYPES
