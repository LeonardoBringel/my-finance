"""Testes unitários dos helpers puros de `components/charts.py` (sem streamlit)."""

from components.charts import donut_chart, expenses_by_day_chart
from utils.theme import EXPENSE_PALETTE, EXPENSE_PALETTE_MUTED


def _day_data(n: int) -> dict[str, dict[int, float]]:
    return {f"Categoria {i}": {1: 10.0} for i in range(n)}


def test_expenses_by_day_chart_uses_the_cycle_in_order():
    fig = expenses_by_day_chart(_day_data(9), "Teste", 2026, 1)
    colors = [trace.marker.color for trace in fig.data]
    assert colors == EXPENSE_PALETTE


def test_expenses_by_day_chart_distinct_up_to_eighteen_categories():
    fig = expenses_by_day_chart(_day_data(18), "Teste", 2026, 1)
    colors = [trace.marker.color for trace in fig.data]
    assert len(colors) == 18
    assert len(set(colors)) == 18


def test_expenses_by_day_chart_second_turn_is_muted():
    fig = expenses_by_day_chart(_day_data(18), "Teste", 2026, 1)
    colors = [trace.marker.color for trace in fig.data]
    assert colors[9:] == EXPENSE_PALETTE_MUTED


def test_expenses_by_day_chart_wraps_predictably_above_eighteen():
    fig = expenses_by_day_chart(_day_data(20), "Teste", 2026, 1)
    colors = [trace.marker.color for trace in fig.data]
    assert colors[18] == colors[0]
    assert colors[19] == colors[1]


def test_expenses_by_day_chart_never_leaves_the_brand_cycle():
    fig = expenses_by_day_chart(_day_data(30), "Teste", 2026, 1)
    colors = {trace.marker.color for trace in fig.data}
    assert colors <= set(EXPENSE_PALETTE) | set(EXPENSE_PALETTE_MUTED)


def test_donut_chart_defaults_to_the_brand_palette():
    fig = donut_chart(["a", "b"], [1.0, 2.0], "Teste")
    assert list(fig.data[0].marker.colors) == EXPENSE_PALETTE


def test_donut_chart_empty_values_renders_placeholder():
    fig = donut_chart([], [], "Teste")
    assert not fig.data
    assert fig.layout.annotations
