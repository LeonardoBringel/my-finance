import streamlit as st
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from auth import require_login

from components.new_transaction import new_transaction_dialog
from components.styles import inject_global_css
inject_global_css()
from utils import fmt, fmt_date, parse_valor

st.set_page_config(page_title="Lançamentos", page_icon="📋", layout="wide")
db.init_db()

st.markdown("""
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
""", unsafe_allow_html=True)

require_login()
user_id = st.session_state["current_user"]["id"]


col_title, col_back = st.columns([4, 1])
with col_title:
    st.markdown("## 📋 Lançamentos")
with col_back:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.pop("show_form", None)
        st.session_state.pop("form_reset_counter", None)
        st.switch_page("app.py")

# ── Filters ────────────────────────────────────────────────────────────────────
with st.expander("🔍 Filtros", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    years = db.get_available_years(user_id)
    with col1:
        year_options = ["Todos"] + [str(y) for y in years]
        f_year_str   = st.selectbox("Ano", year_options)
        f_year       = None if f_year_str == "Todos" else int(f_year_str)
    month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    with col2:
        f_month_name = st.selectbox("Mês", ["Todos"] + month_names)
        f_month      = month_names.index(f_month_name) + 1 if f_month_name != "Todos" else None
    with col3:
        f_type = st.selectbox(
            "Tipo", ["Todos", "entrada", "saida"],
            format_func=lambda x: "Todos" if x == "Todos" else ("💰 Entrada" if x == "entrada" else "💸 Saída")
        )
    with col4:
        f_cat = st.text_input("Categoria (contém)", "")

if st.button("➕ Novo Registro", type="primary"):
    st.session_state["show_form_txn"] = True
    st.session_state.setdefault("form_txn_reset", 0)


# ── New Transaction Dialog ─────────────────────────────────────────────────────
if st.session_state.get("show_form"):
    new_transaction_dialog(user_id)



# ── Edit Transaction Dialog ────────────────────────────────────────────────────
@st.dialog("✏️ Editar Lançamento")
def edit_transaction_dialog(txn):
    all_cats     = db.get_all_categories(user_id)
    current_type = txn.get("type", "saida")

    col1, col2 = st.columns(2)
    with col1:
        tipo = st.selectbox(
            "Tipo *", ["saida", "entrada"],
            format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada",
            index=0 if current_type == "saida" else 1,
            key="edit_tipo"
        )
    with col2:
        data = st.date_input("Data *", value=date.fromisoformat(txn["date"]),
                             format="DD/MM/YYYY")

    valor_str = st.text_input(
        "Valor (R$) *",
        value=f"{txn['value']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        placeholder="ex: 1.250,00"
    )

    cats_filtered  = {c["name"]: c["id"] for c in all_cats if c["type"] in (tipo, "ambos")}
    cat_names_f    = list(cats_filtered.keys())
    current_cat    = txn.get("category", "")
    cat_idx        = cat_names_f.index(current_cat) if current_cat in cat_names_f else 0
    categoria_nome = st.selectbox("Categoria *", cat_names_f, index=cat_idx)

    selected_cat_id = cats_filtered.get(categoria_nome)
    desc_options    = db.get_descriptions_by_category(user_id, selected_cat_id)
    current_desc    = txn.get("description") or ""
    desc_index      = desc_options.index(current_desc) if current_desc in desc_options else None
    descricao       = st.selectbox(
        "Descrição", options=desc_options, index=desc_index,
        accept_new_options=True,
        placeholder="Digite ou selecione uma descrição...",
        key="edit_desc"
    ) or ""

    if txn.get("installment_total"):
        st.info(f"⚠️ Parcela {txn['installment_number']}/{txn['installment_total']} — editar só esta parcela")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salvar", type="primary", use_container_width=True):
            valor_parsed = parse_valor(valor_str) if valor_str else None
            if not valor_parsed or valor_parsed <= 0:
                st.error("Informe um valor válido.")
            else:
                db.update_transaction(
                    user_id=user_id,
                    id_=txn["id"],
                    category_id=cats_filtered[categoria_nome],
                    date_=data.strftime("%Y-%m-%d"),
                    description=descricao,
                    value=valor_parsed,
                )
                st.success("✅ Atualizado!")
                st.session_state.pop("edit_txn", None)
                st.rerun()
    with c2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.pop("edit_txn", None)
            st.rerun()


if "edit_txn" in st.session_state:
    edit_transaction_dialog(st.session_state["edit_txn"])


# ── Load & Filter ──────────────────────────────────────────────────────────────
transactions = db.get_transactions(user_id, year=f_year, month=f_month)
if f_type != "Todos":
    transactions = [t for t in transactions if t["type"] == f_type]
if f_cat:
    transactions = [t for t in transactions if f_cat.lower() in t["category"].lower()]

# ── Summary Metrics ────────────────────────────────────────────────────────────
total_in  = sum(t["value"] for t in transactions if t["type"] == "entrada")
total_out = sum(t["value"] for t in transactions if t["type"] in ("saida", "ambos"))

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Entradas", fmt(total_in))
col2.metric("💸 Total Saídas", fmt(total_out))
col3.metric("📈 Saldo", fmt(total_in - total_out))

st.divider()

# ── Table ──────────────────────────────────────────────────────────────────────
if not transactions:
    st.info("Nenhum lançamento encontrado para os filtros selecionados.")
else:
    st.markdown(f"**{len(transactions)} lançamento(s) encontrado(s)**")
    header = st.columns([1.2, 1.5, 1.8, 2.5, 1.5, 1.2, 0.8, 0.8])
    for h, label in zip(header, ["Tipo", "Data", "Categoria", "Descrição", "Valor", "Parcela", "✏️", "🗑️"]):
        h.markdown(f"**{label}**")
    st.divider()

    for txn in transactions:
        cols       = st.columns([1.2, 1.5, 1.8, 2.5, 1.5, 1.2, 0.8, 0.8])
        tipo       = txn["type"]
        tipo_icon  = "💰" if tipo == "entrada" else "💸"
        tipo_label = "Entrada" if tipo == "entrada" else "Saída"

        cols[0].markdown(f"{tipo_icon} {tipo_label}")
        cols[1].markdown(fmt_date(txn["date"]))
        cols[2].markdown(txn["category"])
        cols[3].markdown(txn["description"] or "—")

        val_color = "green" if tipo == "entrada" else "red"
        cols[4].markdown(f":{val_color}[{fmt(txn['value'])}]")
        cols[5].markdown(
            f"{txn['installment_number']}/{txn['installment_total']}"
            if txn.get("installment_total") else "—"
        )

        if cols[6].button("✏️", key=f"edit_{txn['id']}"):
            st.session_state["edit_txn"] = txn
            st.rerun()

        if cols[7].button("🗑️", key=f"del_{txn['id']}"):
            st.session_state["confirm_del_id"]    = txn["id"]
            st.session_state["confirm_del_label"] = f"{txn['category']} — {fmt(txn['value'])}"

        if st.session_state.get("confirm_del_id") == txn["id"]:
            st.warning(f"⚠️ Confirmar exclusão de **{st.session_state['confirm_del_label']}**?")
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
