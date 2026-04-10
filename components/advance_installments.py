import streamlit as st

from repositories import TransactionsRepository


@st.dialog("⏩ Adiantar Parcelas", width="large")
def advance_installments_dialog(user_id: int) -> None:
    """Dialog de 2 etapas para adiantamento de parcelas futuras para o mês atual.

    Etapa 1: seleciona o grupo de parcelas desejado.
    Etapa 2: define quantas das últimas parcelas serão adiantadas e confirma.

    Args:
        user_id: ID do usuário autenticado.
    """
    step = st.session_state.get("advance_step", 1)

    if step == 1:
        _render_step_1(user_id)
    else:
        _render_step_2(user_id)


def _render_step_1(user_id: int) -> None:
    """Renderiza a etapa 1: listagem dos grupos de parcelas com parcelas futuras."""
    st.caption("Selecione um grupo de parcelas para adiantar ao mês atual.")

    groups = TransactionsRepository.list_installment_groups_with_future_installments(
        user_id
    )

    if not groups:
        st.info("Nenhuma transação parcelada com parcelas futuras encontrada.")
        if st.button("Fechar", use_container_width=True):
            _close_dialog()
        return

    st.divider()

    header_cols = st.columns([3, 2, 2, 1.5])
    for col, label in zip(
        header_cols, ["Descrição", "Categoria", "Parcelas futuras", ""]
    ):
        col.markdown(f"**{label}**")

    st.divider()

    for group in groups:
        desc = group["description"] or "—"
        cols = st.columns([3, 2, 2, 1.5])
        cols[0].markdown(desc)
        cols[1].markdown(group["category"])
        cols[2].markdown(f"{group['future_count']} de {group['installment_total']}")
        if cols[3].button("Selecionar", key=f"sel_{group['installment_group']}"):
            st.session_state["advance_selected_group"] = group
            st.session_state["advance_step"] = 2
            st.rerun(scope="fragment")

    st.divider()
    if st.button("Fechar", use_container_width=True):
        _close_dialog()


def _render_step_2(user_id: int) -> None:
    """Renderiza a etapa 2: seleção da quantidade de parcelas e confirmação."""
    group = st.session_state.get("advance_selected_group", {})

    desc = group.get("description") or "—"
    category = group.get("category", "—")
    future_count = group.get("future_count", 0)
    installment_total = group.get("installment_total", 0)

    st.markdown(f"**{desc}** — {category}")
    st.caption(
        f"Parcelas futuras disponíveis: **{future_count}** de {installment_total} total"
    )
    st.info(
        "As parcelas adiantadas serão as **últimas** do grupo (por número de parcela) "
        "e receberão a data do mês atual mantendo o mesmo dia."
    )

    st.divider()

    count = st.number_input(
        "Quantas parcelas adiantar?",
        min_value=1,
        max_value=future_count,
        value=1,
        step=1,
        key="advance_count",
    )

    st.divider()
    col_confirm, col_back, col_close = st.columns(3)

    with col_confirm:
        if st.button("✅ Confirmar", type="primary", use_container_width=True):
            TransactionsRepository.advance_installments(
                user_id=user_id,
                installment_group=group["installment_group"],
                count=int(count),
            )
            st.success(
                f"✅ {int(count)} parcela(s) de **{desc}** adiantada(s) para o mês atual."
            )
            _close_dialog()

    with col_back:
        if st.button("← Voltar", use_container_width=True):
            st.session_state["advance_step"] = 1
            st.session_state.pop("advance_selected_group", None)
            st.session_state.pop("advance_count", None)
            st.rerun(scope="fragment")

    with col_close:
        if st.button("Fechar", use_container_width=True):
            _close_dialog()


def _close_dialog() -> None:
    """Remove todas as chaves de estado do dialog e fecha-o."""
    st.session_state.pop("show_advance_form", None)
    st.session_state.pop("advance_step", None)
    st.session_state.pop("advance_selected_group", None)
    st.session_state.pop("advance_count", None)
    st.rerun()


def clear_advance_dialog_states() -> None:
    """Remove da session_state chaves órfãs do dialog de adiantamento.

    Chamado no carregamento da página para limpar estado obsoleto quando
    o dialog não está ativo (e.g. usuário navegou para outra página).
    """
    if not st.session_state.get("show_advance_form"):
        st.session_state.pop("advance_step", None)
        st.session_state.pop("advance_selected_group", None)
        st.session_state.pop("advance_count", None)
