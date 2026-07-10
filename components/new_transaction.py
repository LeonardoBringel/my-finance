from datetime import date, datetime

import streamlit as st

from repositories import CategoriesRepository, TransactionsRepository
from utils.category_types import (
    EXPENSE,
    TRANSACTION_TYPES,
    TYPE_LABELS,
    categories_for,
    is_expense,
    selectable_type,
)
from utils.data_format_utils import format_currency, parse_value_text
from utils.i18n import t


@st.dialog(t("components.new_transaction.dialog_title"))
def new_transaction_dialog(user_id: int, txn: dict = None):
    """Dialog unificado para criar ou editar uma transação financeira.

    Args:
        user_id: ID do usuário autenticado.
        txn: Dict da transação existente para modo de edição, ou None para criação.
    """
    is_edit = txn is not None
    all_cats = CategoriesRepository.list_categories(user_id)
    reset_key = st.session_state.get("form_reset_counter", 0)

    # ── Tipo ──────────────────────────────────────────────────────────────────
    default_tipo = (
        txn["type"] if is_edit else st.session_state.get("last_tipo", EXPENSE)
    )
    col1, col2 = st.columns(2)
    with col1:
        tipo = st.selectbox(
            t("components.new_transaction.type"),
            TRANSACTION_TYPES,
            format_func=lambda x: TYPE_LABELS[x],
            index=TRANSACTION_TYPES.index(selectable_type(default_tipo)),
            key=f"tipo_{reset_key}",
        )
    with col2:
        cats_filtered = {
            c["name"]: c["id"]
            for c in all_cats
            if c["type"] in categories_for(tipo)
        }
        current_cat = txn["category"] if is_edit else ""
        cat_list = [""] + list(cats_filtered.keys())
        cat_index = (
            cat_list.index(current_cat) if current_cat in cat_list else 0
        )
        categoria_nome = st.selectbox(
            t("components.new_transaction.category"),
            cat_list,
            index=cat_index,
            key=f"cat_{reset_key}",
        )

    # ── Descrição ─────────────────────────────────────────────────────────────
    selected_cat_id = (
        cats_filtered.get(categoria_nome) if categoria_nome else None
    )
    desc_options = (
        TransactionsRepository.list_descriptions_by_category(
            user_id, selected_cat_id
        )
        if categoria_nome
        else []
    )
    current_desc = (
        txn["description"] if is_edit and txn.get("description") else None
    )
    desc_index = (
        desc_options.index(current_desc)
        if current_desc in desc_options
        else None
    )
    descricao_final = (
        st.selectbox(
            t("components.new_transaction.description"),
            options=desc_options,
            index=desc_index,
            accept_new_options=True,
            placeholder=(
                t(
                    "components.new_transaction.description_placeholder_no_category"
                )
                if not categoria_nome
                else t("components.new_transaction.description_placeholder")
            ),
            key=f"desc_{reset_key}",
            disabled=not categoria_nome,
        )
        or ""
    )

    # ── Data ──────────────────────────────────────────────────────────────────
    default_date = (
        date.fromisoformat(txn["date"]) if is_edit else datetime.today()
    )
    data = st.date_input(
        t("components.new_transaction.date"),
        value=default_date,
        format="DD/MM/YYYY",
    )

    # ── Valor ─────────────────────────────────────────────────────────────────
    default_valor = (
        f"{txn['value']:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
        if is_edit
        else ""
    )

    def _format_valor():
        """Formata o campo de valor no padrão brasileiro ao digitar."""
        raw = st.session_state.get(f"valor_{reset_key}", "")
        digits = "".join(filter(str.isdigit, raw))
        if digits:
            formatted = (
                f"{int(digits) / 100:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
            st.session_state[f"valor_{reset_key}"] = formatted

    valor_str = st.text_input(
        t("components.new_transaction.value"),
        value=default_valor,
        key=f"valor_{reset_key}",
        placeholder=t("components.new_transaction.value_placeholder"),
        on_change=_format_valor,
    )

    # ── Parcelamento (apenas criação de saídas) ───────────────────────────────
    parcelas = 1
    if not is_edit:
        parcelado = st.checkbox(
            t("components.new_transaction.installment_check"),
            key=f"parcelado_{reset_key}",
            disabled=not is_expense(tipo),
            help=(
                None
                if is_expense(tipo)
                else t("components.new_transaction.installment_help")
            ),
        )
        if parcelado and is_expense(tipo):
            parcelas = st.number_input(
                t("components.new_transaction.installment_count"),
                min_value=2,
                max_value=60,
                value=2,
                step=1,
                key=f"parcelas_{reset_key}",
            )
        valor_parsed = parse_value_text(valor_str) if valor_str else None
        if parcelado and valor_parsed and parcelas > 1:
            st.info(
                t(
                    "components.new_transaction.installment_hint",
                    value=format_currency(valor_parsed / parcelas),
                    count=int(parcelas),
                )
            )
    else:
        if txn.get("installment_total"):
            st.info(
                t(
                    "components.new_transaction.editing_installment",
                    number=txn["installment_number"],
                    total=txn["installment_total"],
                )
            )

    # ── Ações ──────────────────────────────────────────────────────────────────
    st.divider()
    col_save, col_cancel = st.columns(2)
    valor_parsed = parse_value_text(valor_str) if valor_str else None

    with col_save:
        label = (
            t("components.new_transaction.save_edit")
            if is_edit
            else t("components.new_transaction.save")
        )
        if st.button(label, type="primary", use_container_width=True):
            if not categoria_nome:
                st.error(t("components.new_transaction.empty_category"))
            elif not valor_parsed or valor_parsed <= 0:
                st.error(t("components.new_transaction.invalid_value"))
            else:
                if is_edit:
                    TransactionsRepository.update_transaction(
                        user_id=user_id,
                        id=txn["id"],
                        category_id=cats_filtered[categoria_nome],
                        date=data.strftime("%Y-%m-%d"),
                        description=descricao_final,
                        value=valor_parsed,
                    )
                    st.success(t("components.new_transaction.updated"))
                    st.session_state.pop("edit_txn", None)
                    st.rerun()
                else:
                    TransactionsRepository.create_transaction(
                        user_id=user_id,
                        category_id=cats_filtered[categoria_nome],
                        date=data.strftime("%Y-%m-%d"),
                        description=descricao_final,
                        value=valor_parsed,
                        installments=int(parcelas),
                    )
                    st.success(t("components.new_transaction.saved"))
                    st.session_state["last_tipo"] = tipo
                    st.session_state["form_reset_counter"] = reset_key + 1
                    st.rerun(scope="fragment")

    with col_cancel:
        if st.button(
            t("components.new_transaction.close"), use_container_width=True
        ):
            st.session_state.pop("show_form", None)
            st.session_state.pop("form_reset_counter", None)
            st.session_state.pop("edit_txn", None)
            st.session_state.pop("last_tipo", None)
            st.rerun()


def clear_transaction_dialog_states() -> None:
    """Remove da session_state as chaves relacionadas ao dialog de nova transação."""
    st.session_state.pop("show_form", None)
    st.session_state.pop("form_reset_counter", None)
