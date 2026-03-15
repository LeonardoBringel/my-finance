import plotly.graph_objects as go
import plotly.express as px

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
    "#4CAF50", "#66BB6A", "#81C784", "#A5D6A7",
    "#FFA726", "#FF7043", "#EF5350", "#AB47BC",
    "#42A5F5", "#26C6DA", "#D4E157", "#8D6E63"
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
        fig.add_annotation(text="Sem dados", x=0.5, y=0.5, showarrow=False,
                           font=dict(color=TEXT_COLOR, size=16))
        fig.update_layout(**_base_layout(title))
        return fig

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors or EXPENSE_COLORS),
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(**_base_layout(title))
    return fig


def bar_chart_expenses(categories, planned, actual, title="Detalhamento Despesas"):
    if not categories:
        fig = go.Figure()
        fig.add_annotation(text="Sem dados", x=0.5, y=0.5, showarrow=False,
                           font=dict(color=TEXT_COLOR, size=16))
        fig.update_layout(**_base_layout(title))
        return fig

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Total",
        x=categories,
        y=actual,
        marker_color=GREEN_MAIN,
        hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>",
    ))
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


def line_chart_trend(months_data, title="Entradas x Saídas (ano)"):
    month_labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                    "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    keys = sorted(months_data.keys())
    entradas = [months_data[k]["entrada"] for k in keys]
    saidas = [months_data[k]["saida"] for k in keys]
    labels = [month_labels[int(k) - 1] for k in keys]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels, y=entradas,
        name="Entradas",
        mode="lines+markers",
        line=dict(color=GREEN_MAIN, width=2),
        marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>Entradas: R$ %{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=labels, y=saidas,
        name="Saídas",
        mode="lines+markers",
        line=dict(color=RED_MAIN, width=2),
        marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>Saídas: R$ %{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(title, showlegend=True),
        legend=dict(font=dict(color=TEXT_COLOR), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_COLOR)),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR,
                   tickprefix="R$", tickfont=dict(color=TEXT_COLOR)),
    )
    return fig


def saldo_gauge(saldo, max_val):
    color = GREEN_MAIN if saldo >= 0 else RED_MAIN
    ratio = max(0, min(1, saldo / max_val)) if max_val else 0

    fig = go.Figure(go.Pie(
        values=[ratio, 1 - ratio],
        hole=0.6,
        marker=dict(colors=[color, "rgba(255,255,255,0.08)"]),
        textinfo="none",
        hoverinfo="skip",
        sort=False,
    ))
    fig.update_layout(**_base_layout())
    return fig
