"""Testes unitários dos helpers puros de `components/charts.py` (sem streamlit)."""

from components.charts import (
    EXPENSE_COLORS,
    _interleaved_order,
    expense_palette,
    expenses_by_day_chart,
)


def test_expense_palette_empty():
    assert expense_palette(0) == []


def test_expense_palette_negative():
    assert expense_palette(-1) == []


def test_expense_palette_single_color_no_zero_division():
    palette = expense_palette(1)
    assert len(palette) == 1
    assert isinstance(palette[0], str) and palette[0]


def test_expense_palette_distinct_for_range_of_n():
    for n in range(1, 31):
        palette = expense_palette(n)
        assert len(palette) == n
        assert len(set(palette)) == n


def test_interleaved_order_no_ramp_neighbors_from_n4():
    for n in range(4, 21):
        order = _interleaved_order(n)
        assert sorted(order) == list(range(n))
        for a, b in zip(order, order[1:]):
            assert abs(a - b) >= 2


def test_expenses_by_day_chart_no_repeated_colors_above_len_expense_colors():
    data = {f"Categoria {i}": {1: 10.0} for i in range(len(EXPENSE_COLORS) + 5)}
    fig = expenses_by_day_chart(data, "Teste", 2026, 1)
    colors = [trace.marker.color for trace in fig.data]
    assert len(colors) == len(data)
    assert len(set(colors)) == len(data)
