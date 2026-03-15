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
    initial_sidebar_state="expanded",
)

db.init_db()

# ── Custom CSS ─────────────────────────────────────────────────────────────────
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
    """R$ 1.234,56"""
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_valor(s):
    """Accept '1.234,56' or '1234.56'"""
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

    tipo = st.selectbox("Tipo *", ["saida", "entrada"],
                        format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada")

    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data *", value=datetime.today(), format="DD/MM/YYYY")
    with col2:
        valor_str = st.text_input(
            "Valor Total (R$) *",
            value="",
            key=f"valor_{reset_key}",
            placeholder="ex: 1.250,00"
        )

    cats_filtered = [c["name"] for c in all_cats if c["type"] in (tipo, "ambos")]
    used_cats = db.get_autocomplete_values("category")
    cat_options = sorted(set(cats_filtered + used_cats))
    categoria = st.selectbox("Categoria *", [""] + cat_options, key=f"cat_{reset_key}")

    desc_options = db.get_autocomplete_values("description")
    descricao = st.selectbox("Descrição", [""] + desc_options, key=f"desc_sel_{reset_key}")
    descricao_custom = st.text_input("Ou digite uma nova descrição",
                                     placeholder="Descrição personalizada...",
                                     key=f"desc_custom_{reset_key}")
    descricao_final = descricao_custom if descricao_custom else descricao

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
            if not categoria:
                st.error("Selecione uma categoria.")
            elif not valor_parsed or valor_parsed <= 0:
                st.error("Informe um valor válido (ex: 1.250,00).")
            else:
                db.add_transaction(
                    type_=tipo,
                    date_=data.strftime("%Y-%m-%d"),
                    category=categoria,
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
    st.metric("📈 Saldo do Mês", fmt(saldo), delta=fmt(saldo),
              delta_color="normal" if saldo >= 0 else "inverse")
with col4:
    sacc = summary["saldo_acumulado"]
    st.metric("🏦 Saldo Acumulado", fmt(sacc), delta=fmt(sacc),
              delta_color="normal" if sacc >= 0 else "inverse")

st.divider()

# ── Charts Row 1 ──────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)
with col_left:
    labels = [r["category"] for r in expenses_by_cat]
    values = [r["total"] for r in expenses_by_cat]
    st.plotly_chart(donut_chart(labels, values, "🔴 Despesas por Categoria"),
                    use_container_width=True, key="donut_exp")
with col_right:
    labels_in = [r["category"] for r in income_by_cat]
    values_in = [r["total"] for r in income_by_cat]
    green_colors = ["#4CAF50", "#66BB6A", "#81C784", "#A5D6A7", "#C8E6C9"]
    st.plotly_chart(donut_chart(labels_in, values_in, "🟢 Entradas por Categoria",
                                colors=green_colors),
                    use_container_width=True, key="donut_inc")

# ── Charts Row 2 ──────────────────────────────────────────────────────────────
col_bar, col_line = st.columns(2)
with col_bar:
    cats = [r["category"] for r in expenses_by_cat]
    vals = [r["total"] for r in expenses_by_cat]
    st.plotly_chart(bar_chart_expenses(cats, vals, vals, "📊 Detalhamento Despesas"),
                    use_container_width=True, key="bar_exp")
with col_line:
    st.plotly_chart(line_chart_trend(trend, "📈 Entradas x Saídas (ano)"),
                    use_container_width=True, key="line_trend")
