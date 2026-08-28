"""Testes unitários do builder puro de CSS de `components/styles.py`.

Cobre `category_pills_css`: cor por posição (mesmo índice de `expense_palette`
usado nos traces do gráfico), ciclo da paleta acima de 9 categorias, escopo
por `.st-key-{key}`, folha vazia com zero categorias e a regra de atenuação
do marcador na pill não selecionada.
"""

from components.styles import category_pills_css
from utils.theme import expense_palette


def test_category_pills_css_uses_expense_palette_color_by_index():
    css = category_pills_css("daily_cats_2026_8", 4)
    colors = expense_palette(4)
    assert colors[0] in css
    assert colors[3] in css


def test_category_pills_css_wraps_the_palette_cycle_above_nine():
    css = category_pills_css("daily_cats_2026_8", 11)
    colors = expense_palette(11)
    assert colors[9] == colors[0]
    assert colors[10] == colors[1]
    assert colors[9] in css
    assert colors[10] in css


def test_category_pills_css_scopes_every_rule_by_the_widget_key():
    key = "daily_cats_2026_8"
    css = category_pills_css(key, 3)
    scope = f".st-key-{key}"
    # nth-of-type só deve aparecer dentro de um seletor escopado pela chave.
    for line in css.splitlines():
        if "nth-of-type" in line:
            assert scope in line


def test_category_pills_css_empty_with_zero_categories():
    assert category_pills_css("daily_cats_2026_8", 0) == ""


def test_category_pills_css_generates_no_orphan_rule_with_zero_categories():
    css = category_pills_css("daily_cats_2026_8", 0)
    assert "nth-of-type(1)" not in css


def test_category_pills_css_dims_the_unselected_marker_instead_of_hiding_it():
    css = category_pills_css("daily_cats_2026_8", 3)
    assert "opacity" in css
    assert 'aria-pressed="true"' in css
