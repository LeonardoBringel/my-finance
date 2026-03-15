import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

import database as db
from components.charts import (
    donut_chart, bar_chart_expenses, line_chart_trend, saldo_gauge
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gestão Financeira",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

db.init_db()

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Force sidebar toggle button visible */
    [data-testid="collapsedControl"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    /* Metric cards */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(76,175,80,0.2);
        border-radius: 12px;
        padding: 16px 20px;
    }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }

    /* Sidebar buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid rgba(76,175,80,0.4);
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: #4CAF50;
        color: #4CAF50;
    }

    /* Chart containers */
    .chart-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px;
        padding: 8px;
        margin-bottom: 12px;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar – Filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Gestão Financeira")
    st.divider()

    years = db.get_available_years()
    current_year = datetime.now().year
    default_year_idx = years.index(current_year) if current_year in years else len(years) - 1

    selected_year = st.selectbox("📅 Ano", years, index=default_year_idx)

    month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    selected_month_name = st.selectbox(
        "📆 Mês",
        month_names,
        index=datetime.now().month - 1
    )
    selected_month = month_names.index(selected_month_name) + 1

    st.divider()

    if st.button("➕ Novo Registro", type="primary", use_container_width=True):
        st.session_state["show_form"] = True

    if st.button("📋 Ver Lançamentos", use_container_width=True):
        st.switch_page("pages/transactions.py")

    if st.button("🏷️ Categorias", use_container_width=True):
        st.switch_page("pages/categories.py")


# ── New Transaction Modal ──────────────────────────────────────────────────────
@st.dialog("➕ Novo Registro")
def new_transaction_dialog():
    all_cats = db.get_all_categories()

    tipo = st.selectbox("Tipo *", ["saida", "entrada"],
                        format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada")

    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data *", value=datetime.today())
    with col2:
        valor = st.number_input("Valor Total (R$) *", min_value=0.01, step=0.01, format="%.2f")

    cats_filtered = [c["name"] for c in all_cats if c["type"] in (tipo, "ambos")]
    used_cats = db.get_autocomplete_values("category")
    cat_options = sorted(set(cats_filtered + used_cats))

    categoria = st.selectbox("Categoria *", [""] + cat_options)

    desc_options = db.get_autocomplete_values("description")
    descricao = st.selectbox("Descrição", [""] + desc_options, index=0)
    descricao_custom = st.text_input("Ou digite uma nova descrição", placeholder="Descrição personalizada...")
    descricao_final = descricao_custom if descricao_custom else descricao

    parcelado = st.checkbox("Parcelado?")
    parcelas = 1
    if parcelado:
        parcelas = st.number_input("Número de parcelas", min_value=2, max_value=60, value=2, step=1)
        st.info(f"💡 Valor por parcela: **R$ {valor / parcelas:,.2f}** × {parcelas}x")

    st.divider()
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 Salvar", type="primary", use_container_width=True):
            if not categoria:
                st.error("Selecione uma categoria.")
            elif valor <= 0:
                st.error("Informe um valor válido.")
            else:
                db.add_transaction(
                    type_=tipo,
                    date_=data.strftime("%Y-%m-%d"),
                    category=categoria,
                    description=descricao_final,
                    value=valor,
                    installments=int(parcelas),
                )
                st.success("✅ Registro salvo com sucesso!")
                st.session_state.pop("show_form", None)
                st.rerun()
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.pop("show_form", None)
            st.rerun()


if st.session_state.get("show_form"):
    new_transaction_dialog()


# ── Load Data ──────────────────────────────────────────────────────────────────
summary = db.get_monthly_summary(selected_year, selected_month)
expenses_by_cat = db.get_expenses_by_category(selected_year, selected_month)
income_by_cat = db.get_income_by_category(selected_year, selected_month)
trend = db.get_monthly_trend(selected_year)


# ── Dashboard Header ───────────────────────────────────────────────────────────
st.markdown(f"### 📊 Dashboard — {selected_month_name} / {selected_year}")
st.divider()

# ── KPI Cards ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

with col1:
    delta = f"+R$ {summary['entradas']:,.2f}" if summary["entradas"] else None
    st.metric("💰 Entradas do Mês", fmt(summary["entradas"]))

with col2:
    st.metric("💸 Despesas do Mês", fmt(summary["saidas"]))

with col3:
    saldo = summary["saldo"]
    st.metric("📈 Saldo do Mês", fmt(saldo),
              delta=fmt(saldo),
              delta_color="normal" if saldo >= 0 else "inverse")

with col4:
    sacc = summary["saldo_acumulado"]
    st.metric("🏦 Saldo Acumulado", fmt(sacc),
              delta=fmt(sacc),
              delta_color="normal" if sacc >= 0 else "inverse")

st.divider()

# ── Charts Row 1 ──────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1])

with col_left:
    # Donut – Expenses by category
    if expenses_by_cat:
        labels = [r["category"] for r in expenses_by_cat]
        values = [r["total"] for r in expenses_by_cat]
    else:
        labels, values = [], []

    fig_donut_exp = donut_chart(labels, values, "🔴 Despesas por Categoria")
    st.plotly_chart(fig_donut_exp, use_container_width=True, key="donut_exp")

with col_right:
    # Donut – Income by category
    if income_by_cat:
        labels_in = [r["category"] for r in income_by_cat]
        values_in = [r["total"] for r in income_by_cat]
    else:
        labels_in, values_in = [], []

    from components.charts import EXPENSE_COLORS
    green_colors = ["#4CAF50", "#66BB6A", "#81C784", "#A5D6A7", "#C8E6C9"]
    fig_donut_inc = donut_chart(labels_in, values_in, "🟢 Entradas por Categoria",
                                 colors=green_colors)
    st.plotly_chart(fig_donut_inc, use_container_width=True, key="donut_inc")

# ── Charts Row 2 ──────────────────────────────────────────────────────────────
col_bar, col_line = st.columns([1, 1])

with col_bar:
    cats = [r["category"] for r in expenses_by_cat]
    vals = [r["total"] for r in expenses_by_cat]
    fig_bar = bar_chart_expenses(cats, vals, vals, "📊 Detalhamento Despesas")
    st.plotly_chart(fig_bar, use_container_width=True, key="bar_exp")

with col_line:
    fig_line = line_chart_trend(trend, "📈 Entradas x Saídas (ano)")
    st.plotly_chart(fig_line, use_container_width=True, key="line_trend")
