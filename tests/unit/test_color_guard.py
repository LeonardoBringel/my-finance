"""Guards que mantêm a identidade visual íntegra ao longo do tempo.

Dois blocos de invariantes:

1. Nenhum literal de cor fora de `utils/theme.py` — hex, `rgb()`/`rgba()`,
   sintaxe `:cor[...]` do Streamlit, ou nome CSS de cor em posição de valor.
2. As propriedades medidas da paleta (arco de matiz, saturação, contraste, ΔE)
   continuam valendo — os números publicados em `.specs/codebase/DESIGN-SYSTEM.md`.

Sem o bloco 1, a paleta se desfaz no primeiro `#FF0000` novo numa page. Sem o
bloco 2, uma cor "parecida" adicionada à lista degrada silenciosamente a
legibilidade dos gráficos.
"""

import colorsys
import math
import re
from pathlib import Path

from utils.theme import (
    BG_DARK,
    EXPENSE_PALETTE,
    EXPENSE_PALETTE_MUTED,
    GREEN_DARK,
    GREEN_LIGHT,
    GREEN_MAIN,
)

ROOT = Path(__file__).resolve().parents[2]
THEME_MODULE = ROOT / "utils" / "theme.py"
SCANNED_DIRS = [ROOT / "pages", ROOT / "components", ROOT / "utils"]
LOCALE_FILE = ROOT / "utils" / "locales" / "pt_BR.json"

# ── Bloco 1: nenhum literal de cor fora de utils/theme.py ─────────────────────
HEX_LITERAL = re.compile(
    r"#(?:[0-9A-Fa-f]{3,4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})\b"
)
FUNC_LITERAL = re.compile(r"\brgba?\(\s*\d")
ST_COLOR_MARKUP = re.compile(
    r":(?:red|orange|yellow|green|blue|violet|gray|grey"
    r"|primary|rainbow)(?:-background)?\["
)
# Nome CSS de cor em posição de valor: `color: red`, `background: white`.
CSS_NAMED = re.compile(
    r"(?:^|[\s;])(?:background|background-color|border-color|color|fill|stroke)"
    r"\s*:\s*(?!\{)(?!var\()(?!transparent\b)(?!inherit\b)(?!currentColor\b)"
    r"[A-Za-z]+\b"
)


def _python_files():
    for directory in SCANNED_DIRS:
        for path in sorted(directory.rglob("*.py")):
            if path != THEME_MODULE:
                yield path


def test_no_hex_color_literal_outside_theme():
    offenders = [
        f"{path.relative_to(ROOT)}: {HEX_LITERAL.findall(path.read_text())}"
        for path in _python_files()
        if HEX_LITERAL.search(path.read_text())
    ]
    assert (
        not offenders
    ), "Literal hex fora de utils/theme.py — use um token:\n" + "\n".join(
        offenders
    )


def test_no_rgb_function_literal_outside_theme():
    offenders = [
        str(path.relative_to(ROOT))
        for path in _python_files()
        if FUNC_LITERAL.search(path.read_text())
    ]
    assert not offenders, (
        "rgb()/rgba() literal fora de utils/theme.py — use rgba(TOKEN, alpha):\n"
        + "\n".join(offenders)
    )


def test_no_streamlit_color_markup():
    """`:cor[...]` só aceita cores nomeadas do Streamlit, nenhuma delas é da marca."""
    targets = list(_python_files()) + [LOCALE_FILE]
    offenders = [
        str(path.relative_to(ROOT))
        for path in targets
        if ST_COLOR_MARKUP.search(path.read_text())
    ]
    assert not offenders, (
        "Sintaxe :cor[...] do Streamlit encontrada — use "
        "t('components.value_colored', color=<token>, value=...):\n"
        + "\n".join(offenders)
    )


def test_no_css_named_color_in_locale():
    """O JSON carrega markup de apresentação; cor ali só via placeholder."""
    offenders = CSS_NAMED.findall(LOCALE_FILE.read_text())
    assert (
        not offenders
    ), f"Nome CSS de cor em pt_BR.json: {offenders} — interpole um token."


def test_no_css_named_color_in_python():
    offenders = [
        f"{path.relative_to(ROOT)}: {CSS_NAMED.findall(path.read_text())}"
        for path in _python_files()
        if CSS_NAMED.search(path.read_text())
    ]
    assert (
        not offenders
    ), "Nome CSS de cor em bloco <style> — interpole um token:\n" + "\n".join(
        offenders
    )


# ── Bloco 2: propriedades medidas da paleta ───────────────────────────────────
def _rgb(hex_color: str) -> tuple[int, int, int]:
    raw = hex_color.lstrip("#")
    return tuple(int(raw[i : i + 2], 16) for i in (0, 2, 4))


def _hsl(hex_color: str) -> tuple[float, float, float]:
    r, g, b = (c / 255 for c in _rgb(hex_color))
    h, ll, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s * 100, ll * 100


def _linear(channel: int) -> float:
    c = channel / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hex_color: str) -> float:
    r, g, b = (_linear(c) for c in _rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _lab(hex_color: str) -> tuple[float, float, float]:
    r, g, b = (_linear(c) for c in _rgb(hex_color))
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def _delta_e(a: str, b: str) -> float:
    la, aa, ba = _lab(a)
    lb, ab, bb = _lab(b)
    return math.sqrt((la - lb) ** 2 + (aa - ab) ** 2 + (ba - bb) ** 2)


ALL_PALETTE = EXPENSE_PALETTE + EXPENSE_PALETTE_MUTED


def test_anchor_is_the_new_transaction_button_color():
    """Trava a âncora: mudar o botão exige revisar a paleta inteira."""
    assert GREEN_MAIN == "#4CAF50"
    assert EXPENSE_PALETTE[0] == GREEN_MAIN


def test_semantic_greens_are_the_marca_column():
    assert (GREEN_LIGHT, GREEN_MAIN, GREEN_DARK) == (
        EXPENSE_PALETTE[7],
        EXPENSE_PALETTE[0],
        EXPENSE_PALETTE[5],
    )


def test_palette_stays_inside_the_brand_hue_arc():
    """Arco de design 92°–152°, com 1° de folga para a quantização em 8 bits.

    Os alvos são exatamente 92/122/152; arredondar cada canal para inteiro
    desloca o matiz reconstruído em até ~0,6°.
    """
    for color in EXPENSE_PALETTE:
        hue, sat, _ = _hsl(color)
        assert 91 <= hue <= 153, f"{color} tem matiz {hue:.1f}° — fora do arco"
        assert (
            35 <= sat <= 47
        ), f"{color} tem saturação {sat:.1f}% — fora da faixa"


def test_every_palette_color_is_legible_on_the_dark_background():
    for color in ALL_PALETTE:
        ratio = _contrast(color, BG_DARK)
        assert ratio >= 3.7, f"{color} tem contraste {ratio:.2f}:1 (mín. 3.7)"


def test_no_two_palette_colors_are_confusable():
    for i, a in enumerate(ALL_PALETTE):
        for b in ALL_PALETTE[i + 1 :]:
            assert _delta_e(a, b) >= 8.0, f"{a} e {b} são próximas demais"


def test_cycle_neighbours_are_far_apart():
    """Segmentos vizinhos de donut/barra empilhada nunca colidem."""
    for a, b in zip(EXPENSE_PALETTE, EXPENSE_PALETTE[1:]):
        assert _delta_e(a, b) >= 19.0, f"{a} → {b} muito próximos no ciclo"


def test_muted_turn_never_degrades_below_the_first_turn():
    assert min(_contrast(c, BG_DARK) for c in EXPENSE_PALETTE_MUTED) >= min(
        _contrast(c, BG_DARK) for c in EXPENSE_PALETTE
    )


def test_muted_turn_preserves_hue():
    for base, muted in zip(EXPENSE_PALETTE, EXPENSE_PALETTE_MUTED):
        assert (
            abs(_hsl(base)[0] - _hsl(muted)[0]) <= 3.0
        ), f"{muted} desviou do matiz de {base}"
