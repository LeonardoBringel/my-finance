import os
import sys
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

import database as db
from auth import logout, require_login
from components.charts import (
    annual_evolution_chart,
    bar_chart_expenses,
    donut_chart,
)
from components.new_transaction import new_transaction_dialog
from utils.data_format_utils import format_currency

st.set_page_config(
    page_title="Gestão Financeira",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()
require_login()

current_user = st.session_state["current_user"]
user_id = current_user["id"]

st.markdown(
    """
<style>
    /* Botões primários em verde */
    [data-testid="stBaseButton-primary"] {
        background-color: #4CAF50 !important;
        border-color: #4CAF50 !important;
        color: white !important;
    }
    [data-testid="stBaseButton-primary"]:hover {
        background-color: #43A047 !important;
        border-color: #43A047 !important;
    }
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(76,175,80,0.2);
        border-radius: 12px;
        padding: 16px 20px;
    }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid rgba(76,175,80,0.4);
        transition: all 0.2s;
    }
    .stButton > button:hover { border-color: #4CAF50; color: #4CAF50; }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 1.5rem; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Gestão Financeira")
    st.markdown(f"👤 **{current_user['username']}**")
    st.divider()

    years = db.get_available_years(user_id)
    current_year = datetime.now().year
    default_year_idx = (
        years.index(current_year) if current_year in years else len(years) - 1
    )
    selected_year = st.selectbox("📅 Ano", years, index=default_year_idx)

    month_names = [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    selected_month_name = st.selectbox(
        "📆 Mês", month_names, index=datetime.now().month - 1
    )
    selected_month = month_names.index(selected_month_name) + 1

    st.divider()

    if st.button("➕ Novo Registro", type="primary", use_container_width=True):
        st.session_state["show_form"] = True
        st.session_state.setdefault("form_reset_counter", 0)

    if st.button("📋 Ver Lançamentos", use_container_width=True):
        st.switch_page("pages/transactions.py")

    if st.button("💵 Fluxo de Caixa", use_container_width=True):
        st.switch_page("pages/cash_flow.py")

    if st.button("🏷️ Categorias", use_container_width=True):
        st.switch_page("pages/categories.py")

    if st.button("👤 Perfil", use_container_width=True):
        st.switch_page("pages/profile.py")

    if current_user.get("is_admin"):
        if st.button("👥 Usuários", use_container_width=True):
            st.switch_page("pages/admin.py")

    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        logout()
        st.switch_page("pages/login.py")


# ── New Transaction Modal ──────────────────────────────────────────────────────
if st.session_state.get("show_form"):
    new_transaction_dialog(user_id)


# ── Load Data ──────────────────────────────────────────────────────────────────
summary = db.get_monthly_summary(user_id, selected_year, selected_month)
expenses_by_cat = db.get_expenses_by_category(user_id, selected_year, selected_month)
income_by_cat = db.get_income_by_category(user_id, selected_year, selected_month)
trend = db.get_monthly_trend(user_id, selected_year)
desc_by_cat = db.get_descriptions_by_category_for_dashboard(
    user_id, selected_year, selected_month
)
annual_data = db.get_annual_evolution(user_id, selected_year)

# ── Dashboard Header ───────────────────────────────────────────────────────────
st.markdown(f"### 📊 Dashboard — {selected_month_name} / {selected_year}")
st.divider()

# ── KPI Cards ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 Entradas do Mês", format_currency(summary["entradas"]))
with col2:
    st.metric("💸 Despesas do Mês", format_currency(summary["saidas"]))
with col3:
    saldo = summary["saldo"]
    st.metric(
        "📈 Saldo do Mês",
        "",
        delta=format_currency(saldo),
        delta_color="normal" if saldo >= 0 else "inverse",
    )
with col4:
    sacc = summary["saldo_acumulado"]
    st.metric(
        "🏦 Saldo Acumulado",
        "",
        delta=format_currency(sacc),
        delta_color="normal" if sacc >= 0 else "inverse",
    )

st.divider()

# ── Charts ─────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)
with col_left:
    labels_in = [r["category"] for r in income_by_cat]
    values_in = [r["total"] for r in income_by_cat]
    st.plotly_chart(
        donut_chart(labels_in, values_in, "📊 Entradas por Categoria"),
        width="stretch",
        key="donut_inc",
    )

with col_right:
    cats = [r["category"] for r in expenses_by_cat]
    vals = [r["total"] for r in expenses_by_cat]
    st.plotly_chart(
        bar_chart_expenses(cats, vals, vals, "📊 Detalhamento Despesas"),
        width="stretch",
        key="bar_exp",
    )

# ── Evolução Anual ────────────────────────────────────────────────────────────
st.plotly_chart(
    annual_evolution_chart(annual_data, f"📈 Evolução Anual — {selected_year}"),
    width="stretch",
    key="annual_evolution",
)

# ── Detalhamento por Categoria ─────────────────────────────────────────────────
st.divider()
st.markdown("### 🔍 Detalhamento por Categoria")

MAX_COLS = 4
cat_names = list(desc_by_cat.keys())

if not cat_names:
    st.info("Nenhuma categoria de saída cadastrada.")
else:
    for row_start in range(0, len(cat_names), MAX_COLS):
        row_cats = cat_names[row_start : row_start + MAX_COLS]
        # Always render MAX_COLS columns — empty ones stay blank
        cols = st.columns(MAX_COLS)
        for i in range(MAX_COLS):
            with cols[i]:
                if i >= len(row_cats):
                    # Empty cell — keep grid uniform
                    st.empty()
                    continue

                cat_name = row_cats[i]
                data = desc_by_cat[cat_name]
                total = data["total"]
                pct = data["pct_of_month"]
                prev = data["total_prev"]

                # ── Stats above chart ──────────────────────────────────────
                if prev > 0:
                    delta_pct = ((total - prev) / prev) * 100
                    delta_str = f"{delta_pct:+.1f}% vs mês anterior"
                    delta_color = "green" if delta_pct <= 0 else "red"
                elif total > 0:
                    delta_str = "Novo este mês"
                    delta_color = "green"
                else:
                    delta_str = "Sem gastos"
                    delta_color = "gray"

                st.markdown(
                    f"**{cat_name}**</br>"
                    f"{format_currency(total)} ({pct:.1f}%)</br>"
                    f"<span style='color:{delta_color};font-size:0.8rem'>{delta_str}</span>",
                    unsafe_allow_html=True,
                )

                # ── Donut ──────────────────────────────────────────────────
                items = data["descriptions"]
                if not items:
                    fig = donut_chart([], [], "")
                else:
                    labels = [i["description"] for i in items]
                    values = [i["total"] for i in items]
                    fig = donut_chart(labels, values, "")
                st.plotly_chart(fig, width="stretch", key=f"donut_cat_{cat_name}")
