"""Testes unitários dos helpers puros de `components/charts.py` (sem streamlit)."""

from components.charts import (
    EXPENSE_COLORS,
    _interleaved_order,
    category_history_chart,
    day_hover_texts,
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


def test_day_hover_texts_orders_segments_descending_with_total():
    data = {
        "Farmácia": {12: 50.0},
        "Viagem": {12: 100.0},
        "Mercado": {12: 0.0},
    }
    blocks = day_hover_texts(data, [12])
    assert len(blocks) == 1
    block = blocks[0]
    assert "Dia 12" in block
    assert "R$ 150,00 total" in block
    viagem_pos = block.index("Viagem")
    farmacia_pos = block.index("Farmácia")
    assert viagem_pos < farmacia_pos
    assert "Mercado" not in block


def test_day_hover_texts_single_category():
    data = {"Mercado": {5: 42.0}}
    blocks = day_hover_texts(data, [5])
    assert "Dia 5" in blocks[0]
    assert "R$ 42,00 total" in blocks[0]
    assert "R$ 42,00 — Mercado" in blocks[0]


def test_day_hover_texts_zeroed_day_has_no_segments():
    data = {"Mercado": {1: 0.0}, "Farmácia": {}}
    blocks = day_hover_texts(data, [1])
    assert "Dia 1" in blocks[0]
    assert "R$ 0,00 total" in blocks[0]
    assert "Mercado" not in blocks[0]
    assert "Farmácia" not in blocks[0]


def test_expenses_by_day_chart_shares_hover_block_across_traces():
    data = {"Viagem": {12: 100.0}, "Farmácia": {12: 50.0}}
    fig = expenses_by_day_chart(data, "Teste", 2026, 1)
    customdatas = [trace.customdata for trace in fig.data]
    assert all(cd == customdatas[0] for cd in customdatas)
    assert "R$ 150,00 total" in customdatas[0][11]


def _fake_history(values):
    """Monta um envelope minimal no formato de get_category_history."""
    series = [
        {"year": 2025, "month": 3 + i, "total": v} for i, v in enumerate(values)
    ]
    total = sum(values)
    return {
        "category": "Mercado",
        "type": "saida",
        "series": series,
        "average": total / len(values) if values else 0.0,
        "total": total,
    }


def test_category_history_chart_bar_values_and_labels():
    history = _fake_history([10.0, 20.0, 0.0, 30.0])
    fig = category_history_chart(history)
    bar = fig.data[0]
    assert list(bar.y) == [10.0, 20.0, 0.0, 30.0]
    assert bar.x[0] == "Mar/25"
    assert bar.x[1] == "Abr/25"


def test_category_history_chart_average_line_is_constant():
    history = _fake_history([10.0, 20.0, 30.0])
    fig = category_history_chart(history)
    avg_trace = fig.data[1]
    assert set(avg_trace.y) == {20.0}
    assert avg_trace.mode == "lines"


def test_category_history_chart_all_zeroed_shows_placeholder():
    history = _fake_history([0.0, 0.0, 0.0])
    fig = category_history_chart(history)
    assert len(fig.data) == 0
    assert fig.layout.annotations[0].text == "Sem dados"
