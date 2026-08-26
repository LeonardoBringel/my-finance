"""Testes dos tokens de cor e do ciclo de paleta em `utils/theme.py`."""

import pytest

from utils.theme import (
    EXPENSE_PALETTE,
    EXPENSE_PALETTE_MUTED,
    GREEN_DARK,
    GREEN_LIGHT,
    GREEN_MAIN,
    expense_palette,
    rgba,
)


@pytest.mark.parametrize("n", [-5, -1, 0])
def test_expense_palette_non_positive_is_empty(n):
    assert expense_palette(n) == []


def test_expense_palette_first_turn_is_the_cycle_in_order():
    assert expense_palette(9) == EXPENSE_PALETTE


@pytest.mark.parametrize("n", range(1, 10))
def test_expense_palette_prefix_is_stable(n):
    """A cor de uma categoria não muda quando outra categoria aparece."""
    assert expense_palette(n) == EXPENSE_PALETTE[:n]


def test_expense_palette_second_turn_is_the_muted_cycle():
    assert expense_palette(18)[9:] == EXPENSE_PALETTE_MUTED


@pytest.mark.parametrize("n", [1, 9, 10, 18])
def test_expense_palette_distinct_up_to_eighteen(n):
    palette = expense_palette(n)
    assert len(palette) == n
    assert len(set(palette)) == n


def test_expense_palette_wraps_after_eighteen():
    palette = expense_palette(19)
    assert palette[18] == palette[0]
    assert len(palette) == 19


def test_expense_palette_never_leaves_the_brand_cycle():
    known = set(EXPENSE_PALETTE) | set(EXPENSE_PALETTE_MUTED)
    assert set(expense_palette(30)) <= known


def test_semantic_greens_alias_the_marca_column():
    """Os verdes semânticos são apelidos da paleta, não hexes independentes."""
    assert GREEN_MAIN == EXPENSE_PALETTE[0] == "#4CAF50"
    assert GREEN_DARK == EXPENSE_PALETTE[5]
    assert GREEN_LIGHT == EXPENSE_PALETTE[7]


def test_rgba_converts_hex_to_css():
    assert rgba("#4CAF50", 0.2) == "rgba(76, 175, 80, 0.2)"
    assert rgba("4CAF50", 1.0) == "rgba(76, 175, 80, 1.0)"
