from datetime import datetime, date
import database as db
import streamlit as st

from utils import parse_valor, fmt


@st.dialog("➕ Novo Registro")
def new_transaction_dialog(user_id: int, txn: dict = None):
    """
    Unified create/edit dialog.
    - txn=None  → create mode
    - txn=dict  → edit mode (fields pre-filled)
    """
    is_edit   = txn is not None
    all_cats  = db.get_all_categories(user_id)
    reset_key = st.session_state.get("form_reset_counter", 0)

    # ── Tipo ──────────────────────────────────────────────────────────────────
    default_tipo = txn["type"] if is_edit else "saida"
    col1, col2 = st.columns(2)
    with col1:
        tipo = st.selectbox(
            "Tipo *", ["saida", "entrada"],
            format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada",
            index=0 if default_tipo == "saida" else 1,
            key=f"tipo_{reset_key}"
        )
    with col2:
        cats_filtered = {c["name"]: c["id"] for c in all_cats if c["type"] in (tipo, "ambos")}
        current_cat   = txn["category"] if is_edit else ""
        cat_list      = [""] + list(cats_filtered.keys())
        cat_index     = cat_list.index(current_cat) if current_cat in cat_list else 0
        categoria_nome = st.selectbox(
            "Categoria *", cat_list,
            index=cat_index,
            key=f"cat_{reset_key}"
        )

    # ── Descrição (bloqueada até categoria ser selecionada) ───────────────────
    selected_cat_id = cats_filtered.get(categoria_nome) if categoria_nome else None
    desc_options    = db.get_descriptions_by_category(user_id, selected_cat_id) if categoria_nome else []
    current_desc    = txn["description"] if is_edit and txn.get("description") else None
    desc_index      = desc_options.index(current_desc) if current_desc in desc_options else None
    descricao_final = st.selectbox(
        "Descrição",
        options=desc_options,
        index=desc_index,
        accept_new_options=True,
        placeholder="Selecione uma categoria primeiro..." if not categoria_nome else "Digite ou selecione uma descrição...",
        key=f"desc_{reset_key}",
        disabled=not categoria_nome,
    ) or ""

    # ── Data ──────────────────────────────────────────────────────────────────
    default_date = date.fromisoformat(txn["date"]) if is_edit else datetime.today()
    data = st.date_input("Data *", value=default_date, format="DD/MM/YYYY")

    # ── Valor ─────────────────────────────────────────────────────────────────
    default_valor = (
        f"{txn['value']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if is_edit else ""
    )

    def _format_valor():
        raw    = st.session_state.get(f"valor_{reset_key}", "")
        digits = ''.join(filter(str.isdigit, raw))
        if digits:
            formatted = f"{int(digits) / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.session_state[f"valor_{reset_key}"] = formatted

    valor_str = st.text_input(
        "Valor Total (R$) *",
        value=default_valor,
        key=f"valor_{reset_key}",
        placeholder="ex: 1.250,00",
        on_change=_format_valor,
    )

    # ── Parcelado (apenas criação + saída) ────────────────────────────────────
    parcelas = 1
    if not is_edit:
        parcelado = st.checkbox(
            "Parcelado?",
            key=f"parcelado_{reset_key}",
            disabled=tipo == "entrada",
            help="Parcelamento disponível apenas para saídas" if tipo == "entrada" else None,
        )
        if parcelado and tipo == "saida":
            parcelas = st.number_input(
                "Número de parcelas", min_value=2, max_value=60,
                value=2, step=1, key=f"parcelas_{reset_key}"
            )
        valor_parsed = parse_valor(valor_str) if valor_str else None
        if parcelado and valor_parsed and parcelas > 1:
            st.info(f"💡 Valor por parcela: **{fmt(valor_parsed / parcelas)}** × {int(parcelas)}x")
    else:
        if txn.get("installment_total"):
            st.info(f"⚠️ Parcela {txn['installment_number']}/{txn['installment_total']} — editar só esta parcela")

    # ── Actions ───────────────────────────────────────────────────────────────
    st.divider()
    col_save, col_cancel = st.columns(2)
    valor_parsed = parse_valor(valor_str) if valor_str else None

    with col_save:
        label = "💾 Salvar alterações" if is_edit else "💾 Salvar"
        if st.button(label, type="primary", use_container_width=True):
            if not categoria_nome:
                st.error("Selecione uma categoria.")
            elif not valor_parsed or valor_parsed <= 0:
                st.error("Informe um valor válido (ex: 1.250,00).")
            else:
                if is_edit:
                    db.update_transaction(
                        user_id=user_id,
                        id_=txn["id"],
                        category_id=cats_filtered[categoria_nome],
                        date_=data.strftime("%Y-%m-%d"),
                        description=descricao_final,
                        value=valor_parsed,
                    )
                    st.success("✅ Lançamento atualizado!")
                    st.session_state.pop("edit_txn", None)
                else:
                    db.add_transaction(
                        user_id=user_id,
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
            st.session_state.pop("edit_txn", None)
            st.rerun()


def clear_transaction_dialog_states():
    st.session_state.pop("show_form", None)
    st.session_state.pop("form_reset_counter", None)
