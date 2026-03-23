import plotly.express as px
import plotly.graph_objects as go

# ── Color palette ──────────────────────────────────────────────────────────────
GREEN_MAIN = "#4CAF50"
GREEN_LIGHT = "#81C784"
GREEN_DARK = "#388E3C"
RED_MAIN = "#EF5350"
ORANGE_MAIN = "#FFA726"
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


def donut_chart(labels, values, title, colors=None):
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


def bar_chart_expenses(categories, planned, actual, title="Detalhamento Despesas"):
    if not categories:
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


    total = sum(actual) if actual else 1
    pct = [v / total * 100 for v in actual]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Total",
            x=categories,
            y=actual,
            marker_color=GREEN_MAIN,
            text=[f"{p:.1f}%" for p in pct],
            textposition="outside",
            textfont=dict(color=TEXT_COLOR, size=11),
            customdata=pct,
            hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<br>%{customdata:.1f}% das despesas<extra></extra>",
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


def annual_evolution_chart(data: list[dict], title="📈 Evolução Anual do Saldo"):
    """
    Combo chart: bars for entrada/saida, line for cumulative saldo.
    data: list of { month_label, entrada, saida, saldo_acumulado }
    """
    if not data or all(d["entrada"] == 0 and d["saida"] == 0 for d in data):
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", x=0.5, y=0.5, showarrow=False,
                           font=dict(color=TEXT_COLOR, size=16))
        fig.update_layout(**_base_layout(title))
        return fig

    labels   = [d["month_label"]     for d in data]
    entradas = [d["entrada"]          for d in data]
    saidas   = [d["saida"]            for d in data]
    saldos   = [d["saldo_acumulado"]  for d in data]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Entradas", x=labels, y=entradas,
        marker_color="#4CAF50", opacity=0.85,
        hovertemplate="<b>%{x}</b><br>Entradas: R$ %{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Saídas", x=labels, y=saidas,
        marker_color="#EF5350", opacity=0.85,
        hovertemplate="<b>%{x}</b><br>Saídas: R$ %{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Saldo Acumulado", x=labels, y=saldos,
        mode="lines+markers",
        line=dict(color="#FFA726", width=2.5),
        marker=dict(size=7),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>Saldo acumulado: R$ %{y:,.2f}<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout(title, showlegend=True),
        barmode="group",
        legend=dict(font=dict(color=TEXT_COLOR), bgcolor="rgba(0,0,0,0)",
                    orientation="h", y=-0.15),
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_COLOR)),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR,
                   tickprefix="R$", tickfont=dict(color=TEXT_COLOR)),
        yaxis2=dict(overlaying="y", side="right",
                    tickprefix="R$", tickfont=dict(color="#FFA726"),
                    showgrid=False),
    )
    return fig


def saldo_gauge(saldo, max_val):
    color = GREEN_MAIN if saldo >= 0 else RED_MAIN
    ratio = max(0, min(1, saldo / max_val)) if max_val else 0

    fig = go.Figure(
        go.Pie(
            values=[ratio, 1 - ratio],
            hole=0.6,
            marker=dict(colors=[color, "rgba(255,255,255,0.08)"]),
            textinfo="none",
            hoverinfo="skip",
            sort=False,
        )
    )
    fig.update_layout(**_base_layout())
    return fig
