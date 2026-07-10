from utils.category_types import ALL_TYPES, TRANSACTION_TYPES
from utils.filters import ALL_FILTER


def test_all_filter_nao_colide_com_tipo_de_dominio():
    """O sentinela nunca pode ser confundido com um tipo real de categoria."""
    assert ALL_FILTER not in ALL_TYPES
    assert ALL_FILTER not in TRANSACTION_TYPES


def test_all_filter_nao_e_um_texto_exibivel():
    """O sentinela é um valor de opção, não um rótulo: nunca chega à tela."""
    assert ALL_FILTER.startswith("__")
    assert ALL_FILTER.endswith("__")
