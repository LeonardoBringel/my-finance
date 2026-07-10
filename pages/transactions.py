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
from utils.category_types import (
    TRANSACTION_TYPES,
    TYPE_LABELS,
    is_expense,
    is_income,
    is_investment,
)
from utils.filters import ALL_FILTER
from utils.i18n import t

inject_global_css()
from utils.data_format_utils import format_currency, format_date

st.set_page_config(
    page_title=t("pages.transactions.page_title"),
    page_icon="📋",
    layout="wide",
)

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
last_day_of_month = today.replace(
    day=calendar.monthrange(today.year, today.month)[1]
)


# ── Onboarding ─────────────────────────────────────────────────────────────────
@st.dialog(t("pages.transactions.onboarding_title"), width="large")
def onboarding_dialog():
    """Dialog de boas-vindas com instruções sobre o registro de lançamentos."""
    st.markdown(t("pages.transactions.onboarding_body"))
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            t("pages.transactions.onboarding_create_first"),
            type="primary",
            use_container_width=True,
        ):
            st.session_state["show_form"] = True
            st.session_state.setdefault("form_reset_counter", 0)
            st.rerun()
    with c2:
        if st.button(
            t("pages.transactions.onboarding_manage_categories"),
            use_container_width=True,
        ):
            st.switch_page("pages/categories.py")


init_onboarding("txn", not TransactionsRepository.has_any_transaction(user_id))

page_header(t("pages.transactions.header"), cleanup_keys=["edit_txn"])

# ── Filter version — incrementar força re-render de todos os widgets ──────────
if "filter_v" not in st.session_state:
    st.session_state["filter_v"] = 0

v = st.session_state["filter_v"]

# ── Filtros ────────────────────────────────────────────────────────────────────
with st.expander(t("pages.transactions.filters"), expanded=True):
    col1, col2 = st.columns([2, 1])

    with col1:
        date_range = st.date_input(
            t("pages.transactions.period"),
            value=(first_day_of_month, last_day_of_month),
            format="DD/MM/YYYY",
            key=f"f_daterange_{v}",
        )

    with col2:
        f_type = st.selectbox(
            t("pages.transactions.type"),
            [ALL_FILTER, *TRANSACTION_TYPES],
            format_func=lambda x: (
                t("common.all") if x == ALL_FILTER else TYPE_LABELS[x]
            ),
            key=f"f_type_{v}",
        )

    col3, col4 = st.columns(2)
    with col3:
        cat_type_filter = None if f_type == ALL_FILTER else f_type
        all_cats = CategoriesRepository.list_categories(
            user_id, type_=cat_type_filter
        )
        cat_options = [ALL_FILTER] + [c["name"] for c in all_cats]
        f_cat_name = st.selectbox(
            t("pages.transactions.category"),
            cat_options,
            format_func=lambda x: (
                t("common.all_feminine") if x == ALL_FILTER else x
            ),
            key=f"f_cat_{v}_{f_type}",
        )
        f_cat_id = next(
            (c["id"] for c in all_cats if c["name"] == f_cat_name), None
        )

    with col4:
        desc_options = TransactionsRepository.list_descriptions_by_category(
            user_id, f_cat_id
        )
        f_desc = st.selectbox(
            t("pages.transactions.description"),
            [ALL_FILTER] + desc_options,
            format_func=lambda x: (
                t("common.all_feminine") if x == ALL_FILTER else x
            ),
            disabled=not f_cat_id,
            help=(
                t("pages.transactions.select_category_first")
                if not f_cat_id
                else None
            ),
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
    if st.button(
        t("pages.transactions.new_record"),
        type="primary",
        use_container_width=True,
    ):
        st.session_state["show_form"] = True
        st.session_state.setdefault("form_reset_counter", 0)
with col_advance:
    if st.button(
        t("pages.transactions.advance_installments"), use_container_width=True
    ):
        st.session_state["show_advance_form"] = True
with col_clear:
    if st.button(
        t("pages.transactions.clear_filters"), use_container_width=True
    ):
        st.session_state["filter_v"] += 1
        st.rerun()

# ── Carregar e filtrar ─────────────────────────────────────────────────────────
transactions = TransactionsRepository.list_transactions(
    user_id, date_from=f_date_from, date_to=f_date_to
)

if f_type != ALL_FILTER:
    transactions = [t for t in transactions if t["type"] == f_type]

if f_cat_name != ALL_FILTER:
    transactions = [t for t in transactions if t["category"] == f_cat_name]

if f_desc != ALL_FILTER:
    transactions = [t for t in transactions if t["description"] == f_desc]

# ── Métricas de resumo ─────────────────────────────────────────────────────────
total_in = sum(t["value"] for t in transactions if is_income(t["type"]))
total_out = sum(t["value"] for t in transactions if is_expense(t["type"]))
total_invest = sum(t["value"] for t in transactions if is_investment(t["type"]))

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("pages.transactions.total_income"), format_currency(total_in))
col2.metric(t("pages.transactions.total_expenses"), format_currency(total_out))
col3.metric(
    t("pages.transactions.total_invested"), format_currency(total_invest)
)
col4.metric(
    t("pages.transactions.balance"), format_currency(total_in - total_out)
)

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
        [
            t("pages.transactions.col_type"),
            t("pages.transactions.col_date"),
            t("pages.transactions.col_category"),
            t("pages.transactions.col_description"),
            t("pages.transactions.col_value"),
            t("pages.transactions.col_installment"),
            "✏️",
            "🗑️",
        ],
    ):
        h.markdown(f"**{label}**")
    st.divider()

    for txn in txns:
        cols = st.columns([1.2, 1.5, 1.8, 2.5, 1.5, 1.2, 0.8, 0.8])
        tipo = txn["type"]
        cols[0].markdown(TYPE_LABELS.get(tipo, tipo))
        cols[1].markdown(format_date(txn["date"]))
        cols[2].markdown(txn["category"])
        cols[3].markdown(txn["description"] or "—")

        val_color = (
            "green"
            if is_income(tipo)
            else "blue" if is_investment(tipo) else "red"
        )
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
            st.session_state["confirm_del_label"] = (
                f"{txn['category']} — {format_currency(txn['value'])}"
            )

        if st.session_state.get("confirm_del_id") == txn["id"]:
            st.warning(
                t(
                    "pages.transactions.confirm_delete",
                    label=st.session_state["confirm_del_label"],
                )
            )
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button(
                t("pages.transactions.confirm"),
                key=f"conf_{txn['id']}",
                type="primary",
            ):
                TransactionsRepository.delete_transaction(user_id, txn["id"])
                st.session_state.pop("confirm_del_id", None)
                st.session_state.pop("confirm_del_label", None)
                st.rerun()
            if c2.button(
                t("pages.transactions.cancel"), key=f"canc_{txn['id']}"
            ):
                st.session_state.pop("confirm_del_id", None)
                st.session_state.pop("confirm_del_label", None)
                st.rerun()


# ── Tabela de lançamentos ──────────────────────────────────────────────────────
if not transactions:
    st.info(t("pages.transactions.none_found"))
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
        st.markdown(t("pages.transactions.past_count", count=len(past_txns)))
        render_txn_table(past_txns)

    if future_txns:
        st.divider()
        st.markdown(t("pages.transactions.future_heading"))
        st.caption(t("pages.transactions.future_count", count=len(future_txns)))
        render_txn_table(future_txns)

    if not past_txns and not future_txns:
        st.info(t("pages.transactions.none_found"))

# ── Dialogs ────────────────────────────────────────────────────────────────────
if st.session_state.pop("txn_show_onboarding", False):
    onboarding_dialog()

if st.session_state.get("show_form"):
    new_transaction_dialog(user_id)

if st.session_state.get("edit_txn"):
    new_transaction_dialog(user_id, txn=st.session_state["edit_txn"])

if st.session_state.get("show_advance_form"):
    advance_installments_dialog(user_id)
