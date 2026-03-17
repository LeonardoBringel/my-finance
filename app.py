import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

import database as db
from auth import require_login, logout
from components.charts import (
    donut_chart, bar_chart_expenses, line_chart_trend
)
from components.new_transaction import new_transaction_dialog
from utils import fmt, fmt_date, parse_valor

st.set_page_config(
    page_title="Gestão Financeira",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()
require_login()

current_user = st.session_state["current_user"]
user_id      = current_user["id"]

st.markdown("""
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
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Gestão Financeira")
    st.markdown(f"👤 **{current_user['username']}**")
    st.divider()

    years = db.get_available_years(user_id)
    current_year = datetime.now().year
    default_year_idx = years.index(current_year) if current_year in years else len(years) - 1
    selected_year = st.selectbox("📅 Ano", years, index=default_year_idx)

    month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    selected_month_name = st.selectbox("📆 Mês", month_names, index=datetime.now().month - 1)
    selected_month = month_names.index(selected_month_name) + 1

    st.divider()

    if st.button("➕ Novo Registro", type="primary", use_container_width=True):
        st.session_state["show_form"] = True
        st.session_state.setdefault("form_reset_counter", 0)

    if st.button("📋 Ver Lançamentos", use_container_width=True):
        st.switch_page("pages/transactions.py")

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
summary          = db.get_monthly_summary(user_id, selected_year, selected_month)
expenses_by_cat  = db.get_expenses_by_category(user_id, selected_year, selected_month)
income_by_cat    = db.get_income_by_category(user_id, selected_year, selected_month)
trend            = db.get_monthly_trend(user_id, selected_year)

# ── Dashboard Header ───────────────────────────────────────────────────────────
st.markdown(f"### 📊 Dashboard — {selected_month_name} / {selected_year}")
st.divider()

# ── KPI Cards ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 Entradas do Mês", fmt(summary["entradas"]))
with col2:
    st.metric("💸 Despesas do Mês", fmt(summary["saidas"]))
with col3:
    saldo = summary["saldo"]
    st.metric("📈 Saldo do Mês", "", delta=fmt(saldo),
              delta_color="normal" if saldo >= 0 else "inverse")
with col4:
    sacc = summary["saldo_acumulado"]
    st.metric("🏦 Saldo Acumulado", "", delta=fmt(sacc),
              delta_color="normal" if sacc >= 0 else "inverse")

st.divider()

# ── Charts ─────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)
with col_left:
    labels_in   = [r["category"] for r in income_by_cat]
    values_in   = [r["total"]    for r in income_by_cat]
    green_colors = ["#4CAF50", "#66BB6A", "#81C784", "#A5D6A7", "#C8E6C9"]
    st.plotly_chart(donut_chart(labels_in, values_in, "📊 Entradas por Categoria",
                                colors=green_colors),
                    width='stretch', key="donut_inc")

with col_right:
    labels = [r["category"] for r in expenses_by_cat]
    values = [r["total"]    for r in expenses_by_cat]
    st.plotly_chart(donut_chart(labels, values, "📊 Despesas por Categoria"),
                    width='stretch', key="donut_exp")

col_line, col_bar = st.columns(2)
with col_bar:
    cats = [r["category"] for r in expenses_by_cat]
    vals = [r["total"]    for r in expenses_by_cat]
    st.plotly_chart(bar_chart_expenses(cats, vals, vals, "📊 Detalhamento Despesas"),
                    width='stretch', key="bar_exp")
with col_line:
    st.plotly_chart(line_chart_trend(trend, "📈 Entradas x Saídas (ano)"),
                    width='stretch', key="line_trend")
