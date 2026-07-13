import calendar

import plotly.express as px
import plotly.graph_objects as go

from utils.i18n import t

# ── Color palette ──────────────────────────────────────────────────────────────
GREEN_MAIN = "#4CAF50"
GREEN_LIGHT = "#81C784"
GREEN_DARK = "#388E3C"
RED_MAIN = "#EF5350"
BG_COLOR = "rgba(0,0,0,0)"
TEXT_COLOR = "#FAFAFA"
GRID_COLOR = "rgba(255,255,255,0.08)"

# Largura de cada barra do gráfico anual, em unidades do eixo X numérico.
# Dois grupos (entrada/saída) por mês → cada um ocupa metade do slot útil.
_BAR_WIDTH = 0.4

# Raio (px) dos cantos das barras preenchidas dos gráficos de barra. Fonte única.
BAR_CORNER_RADIUS = 6
EXPENSE_COLORS = [
    "#1B5E20",
    "#2E7D32",
    "#388E3C",
    "#43A047",
    "#4CAF50",
    "#66BB6A",
    "#81C784",
    "#A5D6A7",
    "#C8E6C9",
    "#E8F5E9",
    "#00695C",
    "#00897B",
    "#26A69A",
    "#80CBC4",
    "#004D40",
]


def _base_layout(title="", showlegend=False):
    return dict(
        title=dict(text=title, font=dict(color=TEXT_COLOR, size=14)),
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR),
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=showlegend,
    )


def donut_chart(labels, values, title, colors=EXPENSE_COLORS):
    if not values or sum(values) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text=t("common.no_data"),
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=TEXT_COLOR, size=16),
        )
        fig.update_layout(**_base_layout(title))
        return fig

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            marker=dict(colors=colors or EXPENSE_COLORS),
            textinfo="percent",
            hovertemplate=t("charts.hover.donut"),
        )
    )
    fig.update_layout(**_base_layout(title))
    return fig


def bar_chart_expenses(categories, values, title: str | None = None):
    """Barras de detalhamento de despesas (+ barra agregada de investimento).

    Args:
        categories: Rótulos das barras (categorias de despesa e, opcionalmente,
            a barra agregada de investimento).
        values: Valores de cada barra, na mesma ordem de ``categories``. O
            denominador dos percentuais é ``sum(values)``, de modo que anexar a
            barra de investimento a ``values`` já produz o denominador
            "despesas + investimentos".
        title: Título do gráfico; usa o padrão do mapping quando omitido.

    Returns:
        go.Figure com uma barra por categoria.
    """
    title = t("charts.expenses_bar_title") if title is None else title
    total = sum(values) if values else 0
    if not categories or total == 0:
        fig = go.Figure()
        fig.add_annotation(
            text=t("common.no_data"),
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=TEXT_COLOR, size=16),
        )
        fig.update_layout(**_base_layout(title))
        return fig

    # Ordena as barras por valor decrescente. A barra agregada de investimento é
    # anexada por último pelo chamador; ordenar aqui garante que ela respeite o
    # ranking em vez de ficar fixa à direita. `sorted` é estável (empate preserva
    # a ordem de entrada) e `sum(values)` do percentual é order-independent.
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    categories = [categories[i] for i in order]
    values = [values[i] for i in order]

    pct = [v / total * 100 for v in values]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name=t("charts.series.total"),
            x=categories,
            y=values,
            marker_color=GREEN_MAIN,
            marker_cornerradius=BAR_CORNER_RADIUS,
            text=[f"{p:.1f}%" for p in pct],
            textposition="outside",
            textfont=dict(color=TEXT_COLOR, size=11),
            customdata=pct,
            hovertemplate=t("charts.hover.expenses_bar"),
        )
    )
    fig.update_layout(
        **_base_layout(title),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_COLOR),
            linecolor=GRID_COLOR,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickprefix="R$",
            tickfont=dict(color=TEXT_COLOR),
        ),
        bargap=0.3,
    )
    return fig


def annual_evolution_chart(data: list[dict], title: str | None = None):
    """
    Combo chart: bars for entrada/saida, line for cumulative saldo.

    A barra de entrada é dividida em duas partes empilhadas no mesmo
    ``offsetgroup`` ("in"): a parte pintada ``max(entrada - investimento, 0)`` e
    a parte investida ``investimento`` (sobreposta acima), desenhada como um
    contorno tracejado de interior vazado. A barra de saídas fica em
    ``offsetgroup`` próprio ("out"), agrupada ao lado — não empilhada.

    data: list of { month_label, entrada, saida, investimento, saldo_acumulado }
    """
    title = t("charts.annual_evolution_title") if title is None else title
    if not data or all(
        d["entrada"] == 0 and d["saida"] == 0 and d["investimento"] == 0
        for d in data
    ):
        fig = go.Figure()
        fig.add_annotation(
            text=t("common.no_data"),
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=TEXT_COLOR, size=16),
        )
        fig.update_layout(**_base_layout(title))
        return fig

    labels = [d["month_label"] for d in data]
    entradas = [d["entrada"] for d in data]
    saidas = [d["saida"] for d in data]
    investimentos = [d["investimento"] for d in data]
    saldos = [d["saldo_acumulado"] for d in data]

    # D-04: pintada estoura para 0 quando investimento > entrada; a parte
    # investida desenha o valor cheio do investimento (sem min()).
    pintada = [max(e - i, 0) for e, i in zip(entradas, investimentos)]
    # % do investimento sobre a entrada do mês, com guarda para entrada == 0.
    invest_pct = [
        (i / e * 100) if e > 0 else 0.0 for e, i in zip(entradas, investimentos)
    ]
    # Hover unificado: a barra pintada e a barra invisível do investimento
    # compartilham o MESMO customdata e template, de modo que o tooltip é idêntico
    # ao passar sobre a parte pintada ou sobre o contorno tracejado.
    hover_data = list(zip(labels, entradas, investimentos, invest_pct))

    # Eixo X numérico com offset/width explícitos: o contorno tracejado da parte
    # investida é desenhado como shape, e shape precisa das coordenadas exatas
    # da barra. Num eixo categórico o Plotly só as resolve no render (JS).
    idx = list(range(len(data)))

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name=t("charts.series.income"),
            x=idx,
            y=pintada,
            offsetgroup="in",
            offset=-_BAR_WIDTH,
            width=_BAR_WIDTH,
            marker_color=GREEN_LIGHT,
            marker_cornerradius=BAR_CORNER_RADIUS,
            opacity=0.85,
            customdata=hover_data,
            hovertemplate=t("charts.hover.income_invested"),
        )
    )
    # Barra invisível: empilha sobre a pintada e serve o tooltip. O visual dela
    # são os shapes tracejados adicionados abaixo (go.Bar não aceita line.dash).
    fig.add_trace(
        go.Bar(
            name=t("charts.series.invested"),
            x=idx,
            y=investimentos,
            offsetgroup="in",
            offset=-_BAR_WIDTH,
            width=_BAR_WIDTH,
            marker=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            customdata=hover_data,
            hovertemplate=t("charts.hover.income_invested"),
        )
    )
    fig.add_trace(
        go.Bar(
            name=t("charts.series.expenses"),
            x=idx,
            y=saidas,
            offsetgroup="out",
            offset=0,
            width=_BAR_WIDTH,
            marker_color=RED_MAIN,
            marker_cornerradius=BAR_CORNER_RADIUS,
            opacity=0.85,
            customdata=labels,
            hovertemplate=t("charts.hover.expenses"),
        )
    )
    fig.add_trace(
        go.Scatter(
            name=t("charts.series.cumulative_balance"),
            x=idx,
            y=saldos,
            mode="lines+markers",
            line=dict(color=GREEN_DARK, width=2.5),
            marker=dict(size=7),
            yaxis="y2",
            customdata=labels,
            hovertemplate=t("charts.hover.cumulative_balance"),
        )
    )

    # Raio dos cantos superiores do contorno tracejado, para casar com o
    # cornerradius (px) das barras. O path usa unidades de dados (não px) e não há
    # a escala do eixo em tempo de montagem, então rx/ry são aproximados: rx é uma
    # fração da largura da barra; ry, uma fração da altura útil do eixo esquerdo.
    # Ajustar por inspeção visual se destoar das barras.
    y_max = max(
        [p + inv for p, inv in zip(pintada, investimentos)] + saidas + [1]
    )
    corner_rx = _BAR_WIDTH * 0.12
    corner_ry = y_max * 0.013

    # Contorno tracejado, interior vazado. Cantos superiores arredondados (arcos
    # quadráticos); a base fica aberta porque se apoia no topo da barra pintada.
    for i, (base, invest) in enumerate(zip(pintada, investimentos)):
        if invest <= 0:
            continue
        x0, x1 = i - _BAR_WIDTH, i
        y0, y1 = base, base + invest
        rx = min(corner_rx, _BAR_WIDTH / 2)
        ry = min(corner_ry, invest)
        fig.add_shape(
            type="path",
            path=(
                f"M {x0},{y0} L {x0},{y1 - ry} Q {x0},{y1} {x0 + rx},{y1} "
                f"L {x1 - rx},{y1} Q {x1},{y1} {x1},{y1 - ry} L {x1},{y0}"
            ),
            line=dict(color=GREEN_LIGHT, width=1.5, dash="dash"),
            fillcolor="rgba(0,0,0,0)",
            xref="x",
            yref="y",
            layer="above",
        )

    fig.update_layout(
        **_base_layout(title),
        barmode="stack",
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_COLOR),
            tickmode="array",
            tickvals=idx,
            ticktext=labels,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickprefix="R$",
            tickfont=dict(color=TEXT_COLOR),
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            tickprefix="R$",
            tickfont=dict(color=TEXT_COLOR),
            showgrid=False,
        ),
    )
    return fig


def expenses_by_day_chart(
    data: dict[str, dict[int, float]], title: str, year: int, month: int
):
    """Stacked bar chart de gastos por categoria por dia do mês.

    Args:
        data: { categoria: { dia: valor } }
        title: Título do gráfico.
        year: Ano selecionado (para calcular dias do mês).
        month: Mês selecionado (1–12).

    Returns:
        go.Figure com barras empilhadas.
    """
    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text=t("common.no_data"),
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=TEXT_COLOR, size=16),
        )
        fig.update_layout(**_base_layout(title))
        return fig

    days_in_month = calendar.monthrange(year, month)[1]
    days = list(range(1, days_in_month + 1))

    fig = go.Figure()
    for i, (cat, day_totals) in enumerate(data.items()):
        values = [day_totals.get(d, 0.0) for d in days]
        color = EXPENSE_COLORS[i % len(EXPENSE_COLORS)]
        fig.add_trace(
            go.Bar(
                name=cat,
                x=days,
                y=values,
                marker_color=color,
                marker_cornerradius=BAR_CORNER_RADIUS,
                hovertemplate=t("charts.hover.by_day", category=cat),
            )
        )

    fig.update_layout(
        **_base_layout(title, showlegend=True),
        barmode="stack",
        legend=dict(
            font=dict(color=TEXT_COLOR),
            bgcolor=BG_COLOR,
            orientation="h",
            y=-0.15,
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_COLOR),
            tickmode="linear",
            dtick=1,
            title=dict(
                text=t("charts.axis.day_of_month"),
                font=dict(color=TEXT_COLOR),
            ),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickprefix="R$",
            tickfont=dict(color=TEXT_COLOR),
        ),
        bargap=0.15,
    )
    return fig
