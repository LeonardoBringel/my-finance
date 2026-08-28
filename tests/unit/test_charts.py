"""Testes unitários dos helpers puros de `components/charts.py` (sem streamlit)."""

from components.charts import donut_chart, expenses_by_day_chart
from utils.data_format_utils import format_currency
from utils.i18n import t
from utils.theme import EXPENSE_PALETTE


def _day_data(n: int) -> dict[str, dict[int, float]]:
    return {f"Categoria {i}": {1: 10.0} for i in range(n)}


def test_expenses_by_day_chart_uses_the_cycle_in_order():
    fig = expenses_by_day_chart(_day_data(9), "Teste", 2026, 1)
    colors = [trace.marker.color for trace in fig.data]
    assert colors == EXPENSE_PALETTE


def test_expenses_by_day_chart_distinct_up_to_nine_categories():
    fig = expenses_by_day_chart(_day_data(9), "Teste", 2026, 1)
    colors = [trace.marker.color for trace in fig.data]
    assert len(colors) == 9
    assert len(set(colors)) == 9


def test_expenses_by_day_chart_wraps_predictably_above_nine():
    fig = expenses_by_day_chart(_day_data(11), "Teste", 2026, 1)
    colors = [trace.marker.color for trace in fig.data]
    assert colors[9] == colors[0]
    assert colors[10] == colors[1]


def test_expenses_by_day_chart_never_leaves_the_brand_ramp():
    fig = expenses_by_day_chart(_day_data(30), "Teste", 2026, 1)
    colors = {trace.marker.color for trace in fig.data}
    assert colors <= set(EXPENSE_PALETTE)


def test_expenses_by_day_chart_visible_none_matches_default():
    data = _day_data(4)
    fig_default = expenses_by_day_chart(data, "Teste", 2026, 1)
    fig_explicit = expenses_by_day_chart(data, "Teste", 2026, 1, visible=None)
    colors_default = [trace.marker.color for trace in fig_default.data]
    colors_explicit = [trace.marker.color for trace in fig_explicit.data]
    assert colors_explicit == colors_default
    customdata_default = [trace.customdata for trace in fig_default.data]
    customdata_explicit = [trace.customdata for trace in fig_explicit.data]
    assert customdata_explicit == customdata_default


def test_expenses_by_day_chart_visible_subset_filters_traces_and_hover_total():
    data = {
        "Categoria 0": {1: 10.0},
        "Categoria 1": {1: 20.0},
        "Categoria 2": {1: 30.0},
    }
    fig = expenses_by_day_chart(
        data, "Teste", 2026, 1, visible=["Categoria 0", "Categoria 1"]
    )
    assert len(fig.data) == 2
    assert {trace.name for trace in fig.data} == {"Categoria 0", "Categoria 1"}
    hover_block = fig.data[0].customdata[0]
    expected_total = t("charts.hover.day_total", value=format_currency(30.0))
    assert expected_total in hover_block
    assert "Categoria 2" not in hover_block


def test_expenses_by_day_chart_visible_subset_preserves_color_of_remaining_categories():
    data = _day_data(4)
    fig_all = expenses_by_day_chart(data, "Teste", 2026, 1)
    fig_subset = expenses_by_day_chart(
        data,
        "Teste",
        2026,
        1,
        visible=["Categoria 1", "Categoria 2", "Categoria 3"],
    )
    color_all = next(
        trace.marker.color
        for trace in fig_all.data
        if trace.name == "Categoria 2"
    )
    color_subset = next(
        trace.marker.color
        for trace in fig_subset.data
        if trace.name == "Categoria 2"
    )
    assert color_all == color_subset


def test_expenses_by_day_chart_visible_empty_list_renders_placeholder():
    fig = expenses_by_day_chart(_day_data(3), "Teste", 2026, 1, visible=[])
    assert not fig.data
    assert fig.layout.annotations


def test_expenses_by_day_chart_visible_ignores_unknown_category_names():
    fig = expenses_by_day_chart(
        _day_data(3), "Teste", 2026, 1, visible=["Categoria 0", "Não Existe"]
    )
    assert len(fig.data) == 1
    assert fig.data[0].name == "Categoria 0"


def test_donut_chart_defaults_to_the_brand_palette():
    fig = donut_chart(["a", "b"], [1.0, 2.0], "Teste")
    assert list(fig.data[0].marker.colors) == EXPENSE_PALETTE


def test_donut_chart_empty_values_renders_placeholder():
    fig = donut_chart([], [], "Teste")
    assert not fig.data
    assert fig.layout.annotations
