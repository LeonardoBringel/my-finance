import os
import sys
from datetime import date, datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from auth import require_login
from components.new_transaction import (
    clear_transaction_dialog_states,
    new_transaction_dialog,
)
from components.styles import inject_global_css

inject_global_css()
from utils.data_format_utils import format_currency, format_date

st.set_page_config(page_title="Lançamentos", page_icon="📋", layout="wide")
db.init_db()

st.markdown(
    """
<style>
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .block-container { padding-top: 1.5rem; }
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(76,175,80,0.2);
        border-radius: 12px;
        padding: 12px 16px;
    }
</style>
""",
    unsafe_allow_html=True,
)

require_login()
clear_transaction_dialog_states()

user_id = st.session_state["current_user"]["id"]
today = date.today()

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

col_title, col_back = st.columns([4, 1])
with col_title:
    st.markdown("## 📋 Lançamentos")
with col_back:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.pop("edit_txn", None)
        st.switch_page("app.py")

# ── Filter version — incrementing this forces all widgets to re-render fresh ──
if "filter_v" not in st.session_state:
    st.session_state["filter_v"] = 0

v = st.session_state["filter_v"]  # shorthand for widget keys

# ── Filters ────────────────────────────────────────────────────────────────────
with st.expander("🔍 Filtros", expanded=True):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        day_options = ["Todos"] + [str(d) for d in range(1, 32)]
        f_day_str = st.selectbox(
            "Dia",
            day_options,
            index=day_options.index(str(today.day)),
            key=f"f_day_{v}",
        )
        f_day = None if f_day_str == "Todos" else int(f_day_str)

    with col2:
        f_month_name = st.selectbox(
            "Mês", ["Todos"] + month_names, index=today.month, key=f"f_month_{v}"
        )
        f_month = (
            month_names.index(f_month_name) + 1 if f_month_name != "Todos" else None
        )

    with col3:
        years = db.get_available_years(user_id)
        year_options = ["Todos"] + [str(y) for y in years]
        default_year = str(today.year)
        f_year_str = st.selectbox(
            "Ano",
            year_options,
            index=year_options.index(default_year)
            if default_year in year_options
            else 0,
            key=f"f_year_{v}",
        )
        f_year = None if f_year_str == "Todos" else int(f_year_str)

    with col4:
        f_type = st.selectbox(
            "Tipo",
            ["Todos", "entrada", "saida"],
            format_func=lambda x: "Todos"
            if x == "Todos"
            else ("💰 Entrada" if x == "entrada" else "💸 Saída"),
            key=f"f_type_{v}",
        )

    all_cats = db.get_all_categories(user_id)
    cat_options = ["Todas"] + [c["name"] for c in all_cats]
    f_cat_name = st.selectbox("Categoria", cat_options, key=f"f_cat_{v}")
    f_cat_id = next((c["id"] for c in all_cats if c["name"] == f_cat_name), None)

    desc_options = (
        db.get_descriptions_by_category(user_id, f_cat_id)
        if f_cat_id
        else db.get_descriptions_by_category(user_id)
    )
    f_desc = st.selectbox(
        "Descrição",
        ["Todas"] + desc_options,
        disabled=not f_cat_id,
        help="Selecione uma categoria primeiro" if not f_cat_id else None,
        key=f"f_desc_{v}",
    )

# ── Action buttons ─────────────────────────────────────────────────────────────
col_new, col_clear = st.columns([1, 1])
with col_new:
    if st.button("➕ Novo Registro", type="primary", use_container_width=True):
        st.session_state["show_form"] = True
        st.session_state.setdefault("form_reset_counter", 0)
with col_clear:
    if st.button("🔄 Limpar Filtros", use_container_width=True):
        st.session_state["filter_v"] += 1
        st.rerun()

# ── Load & Filter ──────────────────────────────────────────────────────────────
transactions = db.get_transactions(user_id, year=f_year, month=f_month)

if f_day:
    transactions = [
        t for t in transactions if datetime.strptime(t["date"], "%Y-%m-%d").day == f_day
    ]

if f_type != "Todos":
    transactions = [t for t in transactions if t["type"] == f_type]

if f_cat_name != "Todas":
    transactions = [t for t in transactions if t["category"] == f_cat_name]

if f_desc != "Todas":
    transactions = [t for t in transactions if t["description"] == f_desc]

# ── Summary Metrics ────────────────────────────────────────────────────────────
total_in = sum(t["value"] for t in transactions if t["type"] == "entrada")
total_out = sum(t["value"] for t in transactions if t["type"] in ("saida", "ambos"))

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Entradas", format_currency(total_in))
col2.metric("💸 Total Saídas", format_currency(total_out))
col3.metric("📈 Saldo", format_currency(total_in - total_out))

st.divider()

# ── Table ──────────────────────────────────────────────────────────────────────
if not transactions:
    st.info("Nenhum lançamento encontrado para os filtros selecionados.")
else:
    st.markdown(f"**{len(transactions)} lançamento(s) encontrado(s)**")
    header = st.columns([1.2, 1.5, 1.8, 2.5, 1.5, 1.2, 0.8, 0.8])
    for h, label in zip(
        header,
        ["Tipo", "Data", "Categoria", "Descrição", "Valor", "Parcela", "✏️", "🗑️"],
    ):
        h.markdown(f"**{label}**")
    st.divider()

    for txn in transactions:
        cols = st.columns([1.2, 1.5, 1.8, 2.5, 1.5, 1.2, 0.8, 0.8])
        tipo = txn["type"]
        tipo_icon = "💰" if tipo == "entrada" else "💸"
        tipo_label = "Entrada" if tipo == "entrada" else "Saída"

        cols[0].markdown(f"{tipo_icon} {tipo_label}")
        cols[1].markdown(format_date(txn["date"]))
        cols[2].markdown(txn["category"])
        cols[3].markdown(txn["description"] or "—")

        val_color = "green" if tipo == "entrada" else "red"
        cols[4].markdown(f":{val_color}[{format_currency(txn['value'])}]")
        cols[5].markdown(
            f"{txn['installment_number']}/{txn['installment_total']}"
            if txn.get("installment_total")
            else "—"
        )

        if cols[6].button("✏️", key=f"edit_{txn['id']}"):
            st.session_state["edit_txn"] = txn
            st.session_state.pop("show_form", None)
            st.rerun()

        if cols[7].button("🗑️", key=f"del_{txn['id']}"):
            st.session_state["confirm_del_id"] = txn["id"]
            st.session_state[
                "confirm_del_label"
            ] = f"{txn['category']} — {format_currency(txn['value'])}"

        if st.session_state.get("confirm_del_id") == txn["id"]:
            st.warning(
                f"⚠️ Confirmar exclusão de **{st.session_state['confirm_del_label']}**?"
            )
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("✅ Confirmar", key=f"conf_{txn['id']}", type="primary"):
                db.delete_transaction(user_id, txn["id"])
                st.session_state.pop("confirm_del_id", None)
                st.session_state.pop("confirm_del_label", None)
                st.rerun()
            if c2.button("❌ Cancelar", key=f"canc_{txn['id']}"):
                st.session_state.pop("confirm_del_id", None)
                st.session_state.pop("confirm_del_label", None)
                st.rerun()

# ── Dialogs (after table so edit_txn is set before rendering) ─────────────────
if st.session_state.get("show_form"):
    new_transaction_dialog(user_id)

if st.session_state.get("edit_txn"):
    new_transaction_dialog(user_id, txn=st.session_state["edit_txn"])
