from utils.category_types import ALL_TYPES, TRANSACTION_TYPES
from utils.filters import ALL_FILTER, sync_all_pill_selection


def test_all_filter_nao_colide_com_tipo_de_dominio():
    """O sentinela nunca pode ser confundido com um tipo real de categoria."""
    assert ALL_FILTER not in ALL_TYPES
    assert ALL_FILTER not in TRANSACTION_TYPES


def test_all_filter_nao_e_um_texto_exibivel():
    """O sentinela é um valor de opção, não um rótulo: nunca chega à tela."""
    assert ALL_FILTER.startswith("__")
    assert ALL_FILTER.endswith("__")


def test_sync_all_pill_marking_all_selects_everything():
    """Marcar a pill Todas (ela entra na seleção) seleciona todas as opções."""
    real = ["A", "B", "C"]
    previous = ["A"]
    selected = ["A", ALL_FILTER]
    result = sync_all_pill_selection(selected, previous, real)
    assert set(result) == {ALL_FILTER, "A", "B", "C"}


def test_sync_all_pill_unmarking_all_deselects_everything():
    """Desmarcar a pill Todas (ela sai da seleção) esvazia a seleção inteira."""
    real = ["A", "B", "C"]
    previous = [ALL_FILTER, "A", "B", "C"]
    selected = ["A", "B", "C"]
    result = sync_all_pill_selection(selected, previous, real)
    assert result == []


def test_sync_all_pill_selecting_last_remaining_option_marks_all():
    """Marcar a última categoria que faltava marca Todas automaticamente."""
    real = ["A", "B", "C"]
    previous = ["A", "B"]
    selected = ["A", "B", "C"]
    result = sync_all_pill_selection(selected, previous, real)
    assert set(result) == {ALL_FILTER, "A", "B", "C"}


def test_sync_all_pill_deselecting_one_option_unmarks_all():
    """Desmarcar uma categoria com Todas marcada desmarca Todas, mantém o resto."""
    real = ["A", "B", "C"]
    previous = [ALL_FILTER, "A", "B", "C"]
    selected = [ALL_FILTER, "A", "C"]
    result = sync_all_pill_selection(selected, previous, real)
    assert set(result) == {"A", "C"}
    assert ALL_FILTER not in result


def test_sync_all_pill_partial_selection_without_full_coverage_stays_unmarked():
    """Seleção parcial que não cobre tudo nunca marca Todas."""
    real = ["A", "B", "C"]
    previous = ["A"]
    selected = ["A", "B"]
    result = sync_all_pill_selection(selected, previous, real)
    assert result == ["A", "B"]


def test_sync_all_pill_result_orders_all_first_then_real_options():
    """A ordem do resultado é sempre [ALL_FILTER] + real_options, nunca outra."""
    real = ["B", "A", "C"]
    previous = ["A"]
    selected = ["A", ALL_FILTER]
    result = sync_all_pill_selection(selected, previous, real)
    assert result == [ALL_FILTER, "B", "A", "C"]
