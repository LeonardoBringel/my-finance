import calendar
import os
import sys
from datetime import date, datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.advance_installments import (
    advance_installments_dialog,
    clear_advance_dialog_states,
)
from components.new_transaction import (
    clear_transaction_dialog_states,
    new_transaction_dialog,
)
from components.styles import (
    init_onboarding,
    inject_global_css,
    inject_subpage_css,
    page_header,
)
from repositories import CategoriesRepository, TransactionsRepository
from utils.auth import require_login

inject_global_css()
from utils.data_format_utils import format_currency, format_date

st.set_page_config(page_title="Lançamentos", page_icon="📋", layout="wide")

inject_subpage_css()
st.markdown(
    """
<style>
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
clear_advance_dialog_states()

user_id = st.session_state["current_user"]["id"]
today = date.today()
first_day_of_month = today.replace(day=1)
last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])


# ── Onboarding ─────────────────────────────────────────────────────────────────
@st.dialog("📋 Bem-vindo aos Lançamentos", width="large")
def onboarding_dialog():
    """Dialog de boas-vindas com instruções sobre o registro de lançamentos."""
    st.markdown(
        """
### O que são Lançamentos?

Os **Lançamentos** são o registro real das suas movimentações financeiras — o que você
efetivamente recebeu ou gastou.

---

### Como funciona?

1. Clique em **➕ Novo Registro** para registrar uma transação.
2. Informe a **categoria**, a **data**, o **valor** e uma descrição opcional.
3. Para compras parceladas, informe o número de parcelas e elas serão criadas automaticamente.

---

### Dicas

- Use os **filtros** para encontrar lançamentos por período, categoria ou tipo.
- As métricas no topo mostram o total de entradas, saídas e saldo do período filtrado.
- O **Dashboard** consolida todos os lançamentos em gráficos e KPIs mensais.

---

💡 **Antes de começar:** Certifique-se de ter criado suas **Categorias** — elas são
necessárias para registrar lançamentos.
    """
    )
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            "➕ Criar Primeiro Lançamento", type="primary", use_container_width=True
        ):
            st.session_state["show_form"] = True
            st.session_state.setdefault("form_reset_counter", 0)
            st.rerun()
    with c2:
        if st.button("🏷️ Gerenciar Categorias", use_container_width=True):
            st.switch_page("pages/categories.py")


init_onboarding("txn", not TransactionsRepository.has_any_transaction(user_id))

page_header("📋 Lançamentos", cleanup_keys=["edit_txn"])

# ── Filter version — incrementar força re-render de todos os widgets ──────────
if "filter_v" not in st.session_state:
    st.session_state["filter_v"] = 0

v = st.session_state["filter_v"]

# ── Filtros ────────────────────────────────────────────────────────────────────
with st.expander("🔍 Filtros", expanded=True):
    col1, col2 = st.columns([2, 1])

    with col1:
        date_range = st.date_input(
            "Período",
            value=(first_day_of_month, last_day_of_month),
            format="DD/MM/YYYY",
            key=f"f_daterange_{v}",
        )

    with col2:
        f_type = st.selectbox(
            "Tipo",
            ["Todos", "entrada", "saida"],
            format_func=lambda x: "Todos"
            if x == "Todos"
            else ("💰 Entrada" if x == "entrada" else "💸 Saída"),
            key=f"f_type_{v}",
        )

    col3, col4 = st.columns(2)
    with col3:
        cat_type_filter = None if f_type == "Todos" else f_type
        all_cats = CategoriesRepository.list_categories(user_id, type_=cat_type_filter)
        cat_options = ["Todas"] + [c["name"] for c in all_cats]
        f_cat_name = st.selectbox("Categoria", cat_options, key=f"f_cat_{v}_{f_type}")
        f_cat_id = next((c["id"] for c in all_cats if c["name"] == f_cat_name), None)

    with col4:
        desc_options = TransactionsRepository.list_descriptions_by_category(
            user_id, f_cat_id
        )
        f_desc = st.selectbox(
            "Descrição",
            ["Todas"] + desc_options,
            disabled=not f_cat_id,
            help="Selecione uma categoria primeiro" if not f_cat_id else None,
            key=f"f_desc_{v}",
        )

# ── Resolve intervalo de datas do filtro ───────────────────────────────────────
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    f_date_from, f_date_to = date_range[0], date_range[1]
elif isinstance(date_range, (list, tuple)) and len(date_range) == 1:
    f_date_from = f_date_to = date_range[0]
else:
    f_date_from = f_date_to = date_range if date_range else first_day_of_month

# ── Botões de ação ─────────────────────────────────────────────────────────────
col_new, col_advance, col_clear = st.columns([1, 1, 1])
with col_new:
    if st.button("➕ Novo Registro", type="primary", use_container_width=True):
        st.session_state["show_form"] = True
        st.session_state.setdefault("form_reset_counter", 0)
with col_advance:
    if st.button("⏩ Adiantar Parcelas", use_container_width=True):
        st.session_state["show_advance_form"] = True
with col_clear:
    if st.button("🔄 Limpar Filtros", use_container_width=True):
        st.session_state["filter_v"] += 1
        st.rerun()

# ── Carregar e filtrar ─────────────────────────────────────────────────────────
transactions = TransactionsRepository.list_transactions(
    user_id, date_from=f_date_from, date_to=f_date_to
)

if f_type != "Todos":
    transactions = [t for t in transactions if t["type"] == f_type]

if f_cat_name != "Todas":
    transactions = [t for t in transactions if t["category"] == f_cat_name]

if f_desc != "Todas":
    transactions = [t for t in transactions if t["description"] == f_desc]

# ── Métricas de resumo ─────────────────────────────────────────────────────────
total_in = sum(t["value"] for t in transactions if t["type"] == "entrada")
total_out = sum(t["value"] for t in transactions if t["type"] in ("saida", "ambos"))

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Entradas", format_currency(total_in))
col2.metric("💸 Total Saídas", format_currency(total_out))
col3.metric("📈 Saldo", format_currency(total_in - total_out))

st.divider()


# ── Renderização da tabela de lançamentos ──────────────────────────────────────
def render_txn_table(txns: list[dict]) -> None:
    """Renderiza a tabela de lançamentos com colunas de edição e exclusão.

    Args:
        txns: Lista de dicts de transações a exibir.
    """
    header = st.columns([1.2, 1.5, 1.8, 2.5, 1.5, 1.2, 0.8, 0.8])
    for h, label in zip(
        header,
        ["Tipo", "Data", "Categoria", "Descrição", "Valor", "Parcela", "✏️", "🗑️"],
    ):
        h.markdown(f"**{label}**")
    st.divider()

    for txn in txns:
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
                TransactionsRepository.delete_transaction(user_id, txn["id"])
                st.session_state.pop("confirm_del_id", None)
                st.session_state.pop("confirm_del_label", None)
                st.rerun()
            if c2.button("❌ Cancelar", key=f"canc_{txn['id']}"):
                st.session_state.pop("confirm_del_id", None)
                st.session_state.pop("confirm_del_label", None)
                st.rerun()


# ── Tabela de lançamentos ──────────────────────────────────────────────────────
if not transactions:
    st.info("Nenhum lançamento encontrado para os filtros selecionados.")
else:
    past_txns = [
        t
        for t in transactions
        if datetime.strptime(t["date"], "%Y-%m-%d").date() <= today
    ]
    future_txns = [
        t
        for t in transactions
        if datetime.strptime(t["date"], "%Y-%m-%d").date() > today
    ]

    if past_txns:
        st.markdown(f"**{len(past_txns)} lançamento(s) registrado(s)**")
        render_txn_table(past_txns)

    if future_txns:
        st.divider()
        st.markdown(f"### 🔮 Lançamentos Futuros")
        st.caption(f"{len(future_txns)} lançamento(s) agendado(s) após hoje")
        render_txn_table(future_txns)

    if not past_txns and not future_txns:
        st.info("Nenhum lançamento encontrado para os filtros selecionados.")

# ── Dialogs ────────────────────────────────────────────────────────────────────
if st.session_state.pop("txn_show_onboarding", False):
    onboarding_dialog()

if st.session_state.get("show_form"):
    new_transaction_dialog(user_id)

if st.session_state.get("edit_txn"):
    new_transaction_dialog(user_id, txn=st.session_state["edit_txn"])

if st.session_state.get("show_advance_form"):
    advance_installments_dialog(user_id)
