"""Testes dos tokens de cor e do ciclo de paleta em `utils/theme.py`."""

import pytest

from utils.theme import (
    EXPENSE_PALETTE,
    GREEN_DARK,
    GREEN_LIGHT,
    GREEN_MAIN,
    GREEN_RAMP,
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


@pytest.mark.parametrize("n", [1, 5, 9])
def test_expense_palette_distinct_up_to_nine(n):
    palette = expense_palette(n)
    assert len(palette) == n
    assert len(set(palette)) == n


def test_expense_palette_wraps_after_nine():
    palette = expense_palette(10)
    assert palette[9] == palette[0]
    assert len(palette) == 10


def test_expense_palette_never_leaves_the_ramp():
    assert set(expense_palette(30)) <= set(GREEN_RAMP)


def test_semantic_greens_are_ramp_steps():
    """Os verdes semânticos são degraus da rampa, não hexes independentes."""
    assert GREEN_MAIN == GREEN_RAMP[4] == "#4CAF50"
    assert GREEN_DARK == GREEN_RAMP[2]
    assert GREEN_LIGHT == GREEN_RAMP[6]


def test_rgba_converts_hex_to_css():
    assert rgba("#4CAF50", 0.2) == "rgba(76, 175, 80, 0.2)"
    assert rgba("4CAF50", 1.0) == "rgba(76, 175, 80, 1.0)"
