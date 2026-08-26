"""Fonte única dos tokens de cor da aplicação.

A âncora da identidade visual é `GREEN_MAIN` (`#4CAF50`) — a cor de fundo do
botão "Novo Registro". Toda cor de marca do sistema é uma derivação dela.

A paleta categórica é **monocromática**: um único verde, o da âncora — matiz
122° e saturação 39%, os valores exatos do botão — em 9 degraus de luminosidade
gravados aqui como hex explícito (sem cálculo de cor em runtime).

Os degraus são espaçados de forma perceptualmente uniforme, em `L*` de Lab e não
em `L` de HSL: espaçar em HSL agrupa os tons claros e espalha os escuros. O passo
500 é literalmente `#4CAF50`.

A ordem de uso (`EXPENSE_PALETTE`) **não** percorre a rampa em sequência — ela
intercala pares e ímpares, de modo que cada cor salta dois degraus em relação à
anterior. É isso que mantém fatias vizinhas de donut distinguíveis sem recorrer
a outra matiz: em sequência o ΔE entre vizinhas seria 4,9; intercalado, é 8,7.
Reordenar a lista quebra essa propriedade.

Referência completa: `.specs/codebase/DESIGN-SYSTEM.md`.
Contrato automatizado: `tests/unit/test_color_guard.py`.
"""


def rgba(hex_color: str, alpha: float) -> str:
    """Converte um token hex em string `rgba(r, g, b, a)` para uso em CSS.

    Args:
        hex_color: Cor no formato `#RRGGBB`.
        alpha: Opacidade entre 0.0 e 1.0.

    Returns:
        String `rgba(r, g, b, alpha)` pronta para um bloco `<style>`.
    """
    raw = hex_color.lstrip("#")
    r, g, b = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


# ── Base do tema ───────────────────────────────────────────────────────────────
# Fundo do tema escuro do Streamlit. É a base de todo contraste medido na
# paleta — mudá-lo invalida os números documentados em DESIGN-SYSTEM.md.
BG_DARK = "#0E1117"
WHITE = "#FFFFFF"

TEXT_COLOR = "#FAFAFA"
TEXT_MUTED = "#8A9A8C"  # delta neutro nos cards ("sem despesas")
TEXT_FAINT = rgba(WHITE, 0.15)  # rodapé de versão no login

# ── Paleta categórica ──────────────────────────────────────────────────────────
# A rampa, do escuro ao claro. Só existe para documentar os degraus e para o
# guard test; o consumo é sempre via EXPENSE_PALETTE.
GREEN_RAMP = [
    "#377E39",  # 900
    "#3C893F",  # 800
    "#419745",  # 700
    "#47A24A",  # 600
    "#4CAF50",  # 500 — âncora, cor do botão Novo Registro
    "#5FB963",  # 400
    "#76C379",  # 300
    "#8BCD8E",  # 200
    "#A2D6A4",  # 100
]

# Ordem de uso: degraus intercalados (pares, depois ímpares). Não reordenar.
EXPENSE_PALETTE = [
    GREEN_RAMP[0],  # 900
    GREEN_RAMP[2],  # 700
    GREEN_RAMP[4],  # 500 — âncora
    GREEN_RAMP[6],  # 300
    GREEN_RAMP[8],  # 100
    GREEN_RAMP[1],  # 800
    GREEN_RAMP[3],  # 600
    GREEN_RAMP[5],  # 400
    GREEN_RAMP[7],  # 200
]

# ── Tokens semânticos ──────────────────────────────────────────────────────────
# Os três verdes são degraus da rampa, não hexes independentes: é o que impede
# dois "verdes escuros" ligeiramente diferentes no sistema.
GREEN_LIGHT = GREEN_RAMP[6]  # 300 — #76C379
GREEN_MAIN = GREEN_RAMP[4]  # 500 — #4CAF50
# O 700, e não o 800, porque GREEN_DARK também pinta texto (valor de
# investimento em Lançamentos): 5,16:1 atende WCAG AA, o 800 (4,36:1) não.
GREEN_DARK = GREEN_RAMP[2]  # 700 — #419745

# Único token fora do arco verde, e de propósito: vermelho de saída é semântica,
# não identidade visual.
RED_MAIN = "#EF5350"

# ── Chrome dos gráficos ────────────────────────────────────────────────────────
CHART_TRANSPARENT = "rgba(0, 0, 0, 0)"
CHART_BG = CHART_TRANSPARENT
CHART_GRID = rgba(WHITE, 0.08)


def expense_palette(n: int) -> list[str]:
    """Retorna n cores do ciclo monocromático da marca.

    A rampa tem 9 degraus. Acima de 9 o ciclo reinicia com repetição — a legenda
    do gráfico desambigua. Não há segunda volta esmaecida: dessaturar um verde
    único produz cinza, não "verde esmaecido", e a marca se perde.

    Args:
        n: Quantidade de cores a retornar.

    Returns:
        Lista de n hex; vazia quando `n <= 0`.
    """
    if n <= 0:
        return []
    return [EXPENSE_PALETTE[i % len(EXPENSE_PALETTE)] for i in range(n)]
