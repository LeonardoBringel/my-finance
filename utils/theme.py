"""Fonte única dos tokens de cor da aplicação.

A âncora da identidade visual é `GREEN_MAIN` (`#4CAF50`) — a cor de fundo do
botão "Novo Registro". Toda cor de marca do sistema é uma derivação dela.

A paleta categórica é uma grade de 3 famílias de matiz × 3 tons, gerada a partir
da âncora e gravada aqui como hex explícito (sem cálculo de cor em runtime):

    matiz ∈ {92°, 122°, 152°} × (S, L) ∈ {(44, 34), (40, 49), (38, 64)}

O arco de 92°–152° é o mais largo que ainda lê como a mesma família de verde. A
ordem de `EXPENSE_PALETTE` alterna família e tom a cada passo, para que
segmentos vizinhos de donut ou de barra empilhada nunca caiam na mesma família
nem no mesmo nível de luz — reordenar a lista quebra essa propriedade.

A segunda volta (`EXPENSE_PALETTE_MUTED`) é a mesma grade dessaturada
(`S × 0.55`, `L` puxada 35% em direção a 46%). Não é opacidade de propósito:
alpha mescla a cor em direção ao fundo escuro e apaga os tons 700.

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
# Ordem de ciclo: alterna família e tom a cada passo. Não reordenar.
EXPENSE_PALETTE = [
    "#4CAF50",  # Marca 500 — âncora, cor do botão Novo Registro
    "#80C6A6",  # Menta 300
    "#547D31",  # Lima 700
    "#4BAF80",  # Menta 500
    "#A1C680",  # Lima 300
    "#317D33",  # Marca 700
    "#7AAF4B",  # Lima 500
    "#80C683",  # Marca 300
    "#317D59",  # Menta 700
]

# Segunda volta (10ª a 18ª categoria): as mesmas 9 cores dessaturadas.
EXPENSE_PALETTE_MUTED = [
    "#609562",  # Marca 500 esmaecida
    "#7CAA95",  # Menta 300 esmaecida
    "#60794A",  # Lima 700 esmaecida
    "#5F957C",  # Menta 500 esmaecida
    "#92AA7C",  # Lima 300 esmaecida
    "#4A794B",  # Marca 700 esmaecida
    "#79955F",  # Lima 500 esmaecida
    "#7CAA7E",  # Marca 300 esmaecida
    "#4A7963",  # Menta 700 esmaecida
]

# ── Tokens semânticos ──────────────────────────────────────────────────────────
# Os três verdes são apelidos da coluna Marca da grade, não hexes independentes:
# é o que impede dois "verdes escuros" ligeiramente diferentes no sistema.
GREEN_LIGHT = EXPENSE_PALETTE[7]  # Marca 300 — #80C683
GREEN_MAIN = EXPENSE_PALETTE[0]  # Marca 500 — #4CAF50
GREEN_DARK = EXPENSE_PALETTE[5]  # Marca 700 — #317D33

# Único token fora do arco verde, e de propósito: vermelho de saída é semântica,
# não identidade visual.
RED_MAIN = "#EF5350"

# ── Chrome dos gráficos ────────────────────────────────────────────────────────
CHART_TRANSPARENT = "rgba(0, 0, 0, 0)"
CHART_BG = CHART_TRANSPARENT
CHART_GRID = rgba(WHITE, 0.08)


def expense_palette(n: int) -> list[str]:
    """Retorna n cores do ciclo da marca, esmaecendo a partir da 10ª.

    Da 1ª à 9ª categoria usa `EXPENSE_PALETTE`; da 10ª à 18ª, a segunda volta
    dessaturada. Acima de 18 o ciclo reinicia com repetição — a legenda do
    gráfico desambigua.

    Args:
        n: Quantidade de cores a retornar.

    Returns:
        Lista de n hex; vazia quando `n <= 0`.
    """
    if n <= 0:
        return []
    ciclo = EXPENSE_PALETTE + EXPENSE_PALETTE_MUTED
    return [ciclo[i % len(ciclo)] for i in range(n)]
