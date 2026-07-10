import calendar

import plotly.express as px
import plotly.graph_objects as go

# ── Color palette ──────────────────────────────────────────────────────────────
GREEN_MAIN = "#4CAF50"
GREEN_LIGHT = "#81C784"
GREEN_DARK = "#388E3C"
RED_MAIN = "#EF5350"
INVEST_MAIN = "#42A5F5"
BG_COLOR = "rgba(0,0,0,0)"
TEXT_COLOR = "#FAFAFA"
GRID_COLOR = "rgba(255,255,255,0.08)"
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
            text="Sem dados",
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
            hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout(title))
    return fig


def bar_chart_expenses(
    categories,
    values,
    title="Detalhamento Despesas",
    investment_label: str | None = None,
):
    """Barras de detalhamento de despesas (+ barra agregada de investimento).

    Args:
        categories: Rótulos das barras (categorias de despesa e, opcionalmente,
            a barra agregada de investimento).
        values: Valores de cada barra, na mesma ordem de ``categories``. O
            denominador dos percentuais é ``sum(values)``, de modo que anexar a
            barra de investimento a ``values`` já produz o denominador
            "despesas + investimentos".
        title: Título do gráfico.
        investment_label: Rótulo da barra de investimento; essa barra recebe a
            cor ``INVEST_MAIN`` e as demais ``GREEN_MAIN``. ``None`` pinta tudo
            de verde.

    Returns:
        go.Figure com uma barra por categoria.
    """
    total = sum(values) if values else 0
    if not categories or total == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Sem dados",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=TEXT_COLOR, size=16),
        )
        fig.update_layout(**_base_layout(title))
        return fig

    pct = [v / total * 100 for v in values]
    colors = [
        INVEST_MAIN if c == investment_label else GREEN_MAIN for c in categories
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Total",
            x=categories,
            y=values,
            marker_color=colors,
            text=[f"{p:.1f}%" for p in pct],
            textposition="outside",
            textfont=dict(color=TEXT_COLOR, size=11),
            customdata=pct,
            hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<br>%{customdata:.1f}% do mês<extra></extra>",
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


def annual_evolution_chart(
    data: list[dict], title="📈 Evolução Anual do Saldo"
):
    """
    Combo chart: bars for entrada/saida, line for cumulative saldo.

    A barra de entrada é dividida em duas partes empilhadas no mesmo
    ``offsetgroup`` ("in"): a parte pintada ``max(entrada - investimento, 0)`` e
    a parte pontilhada ``investimento`` (sobreposta acima). A barra de saídas
    fica em ``offsetgroup`` próprio ("out"), agrupada ao lado — não empilhada.

    data: list of { month_label, entrada, saida, investimento, saldo_acumulado }
    """
    if not data or all(
        d["entrada"] == 0 and d["saida"] == 0 and d["investimento"] == 0
        for d in data
    ):
        fig = go.Figure()
        fig.add_annotation(
            text="Sem dados",
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

    # D-04: pintada estoura para 0 quando investimento > entrada; a pontilhada
    # desenha o valor cheio do investimento (sem min()).
    pintada = [max(e - i, 0) for e, i in zip(entradas, investimentos)]
    # % do investimento sobre a entrada do mês, com guarda para entrada == 0.
    invest_pct = [
        (i / e * 100) if e > 0 else 0.0 for e, i in zip(entradas, investimentos)
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Entradas",
            x=labels,
            y=pintada,
            offsetgroup="in",
            marker_color=GREEN_LIGHT,
            opacity=0.85,
            customdata=entradas,
            hovertemplate="<b>%{x}</b><br>Entradas: R$ %{customdata:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Investido",
            x=labels,
            y=investimentos,
            offsetgroup="in",
            marker=dict(
                color="rgba(0,0,0,0)",
                line=dict(color=GREEN_LIGHT, width=1.5),
                pattern=dict(
                    shape=".",
                    fgcolor=GREEN_LIGHT,
                    bgcolor="rgba(0,0,0,0)",
                    size=3,
                    solidity=0.3,
                ),
            ),
            customdata=invest_pct,
            hovertemplate="<b>%{x}</b><br>Investido: R$ %{y:,.2f}<br>%{customdata:.1f}% da entrada<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Saídas",
            x=labels,
            y=saidas,
            offsetgroup="out",
            marker_color=RED_MAIN,
            opacity=0.85,
            hovertemplate="<b>%{x}</b><br>Saídas: R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Saldo Acumulado",
            x=labels,
            y=saldos,
            mode="lines+markers",
            line=dict(color=GREEN_DARK, width=2.5),
            marker=dict(size=7),
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Saldo acumulado: R$ %{y:,.2f}<extra></extra>",
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
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_COLOR)),
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
            text="Sem dados",
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
                hovertemplate=f"<b>{cat}</b><br>Dia %{{x}}<br>R$ %{{y:,.2f}}<extra></extra>",
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
            title=dict(text="Dia do mês", font=dict(color=TEXT_COLOR)),
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
