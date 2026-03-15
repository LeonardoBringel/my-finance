import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

import database as db
from components.charts import (
    donut_chart, bar_chart_expenses, line_chart_trend, saldo_gauge
)

st.set_page_config(
    page_title="Gestão Financeira",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

st.markdown("""
<style>
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


# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_valor(s):
    s = s.strip().replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Gestão Financeira")
    st.divider()

    years = db.get_available_years()
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


# ── New Transaction Modal ──────────────────────────────────────────────────────
@st.dialog("➕ Novo Registro")
def new_transaction_dialog():
    all_cats = db.get_all_categories()
    reset_key = st.session_state.get("form_reset_counter", 0)

    col1, col2 = st.columns(2)
    with col1:
        tipo = st.selectbox(
            "Tipo *", ["saida", "entrada"],
            format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada",
            key=f"tipo_{reset_key}"
        )
    with col2:
        data = st.date_input("Data *", value=datetime.today(), format="DD/MM/YYYY")

    valor_str = st.text_input(
        "Valor Total (R$) *", value="",
        key=f"valor_{reset_key}", placeholder="ex: 1.250,00"
    )

    # Filter categories by selected type
    cats_filtered = {c["name"]: c["id"] for c in all_cats if c["type"] in (tipo, "ambos")}
    categoria_nome = st.selectbox("Categoria *", [""] + list(cats_filtered.keys()), key=f"cat_{reset_key}")

    selected_cat_id = cats_filtered.get(categoria_nome)
    desc_options = db.get_descriptions_by_category(selected_cat_id)
    descricao_final = st.selectbox(
        "Descrição",
        options=desc_options,
        index=None,
        accept_new_options=True,
        placeholder="Digite ou selecione uma descrição...",
        key=f"desc_{reset_key}"
    ) or ""

    parcelado = st.checkbox("Parcelado?", key=f"parcelado_{reset_key}")
    parcelas = 1
    if parcelado:
        parcelas = st.number_input("Número de parcelas", min_value=2, max_value=60,
                                   value=2, step=1, key=f"parcelas_{reset_key}")

    valor_parsed = parse_valor(valor_str) if valor_str else None
    if parcelado and valor_parsed:
        st.info(f"💡 Valor por parcela: **{fmt(valor_parsed / parcelas)}** × {int(parcelas)}x")

    st.divider()
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 Salvar", type="primary", use_container_width=True):
            if not categoria_nome:
                st.error("Selecione uma categoria.")
            elif not valor_parsed or valor_parsed <= 0:
                st.error("Informe um valor válido (ex: 1.250,00).")
            else:
                db.add_transaction(
                    category_id=cats_filtered[categoria_nome],
                    date_=data.strftime("%Y-%m-%d"),
                    description=descricao_final,
                    value=valor_parsed,
                    installments=int(parcelas),
                )
                st.success("✅ Registro salvo! Preencha o próximo ou feche.")
                st.session_state["form_reset_counter"] = reset_key + 1
                st.rerun()
    with col_cancel:
        if st.button("Fechar", use_container_width=True):
            st.session_state.pop("show_form", None)
            st.session_state.pop("form_reset_counter", None)
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
    labels_in = [r["category"] for r in income_by_cat]
    values_in = [r["total"] for r in income_by_cat]
    green_colors = ["#4CAF50", "#66BB6A", "#81C784", "#A5D6A7", "#C8E6C9"]
    st.plotly_chart(donut_chart(labels_in, values_in, "📊 Entradas por Categoria",
                                colors=green_colors),
                    width='stretch', key="donut_inc")

with col_right:
    labels = [r["category"] for r in expenses_by_cat]
    values = [r["total"] for r in expenses_by_cat]
    st.plotly_chart(donut_chart(labels, values, "📊 Despesas por Categoria"),
                    width='stretch', key="donut_exp")

col_line, col_bar = st.columns(2)
with col_bar:
    cats = [r["category"] for r in expenses_by_cat]
    vals = [r["total"] for r in expenses_by_cat]
    st.plotly_chart(bar_chart_expenses(cats, vals, vals, "📊 Detalhamento Despesas"),
                    width='stretch', key="bar_exp")
with col_line:
    st.plotly_chart(line_chart_trend(trend, "📈 Entradas x Saídas (ano)"),
                    width='stretch', key="line_trend")
