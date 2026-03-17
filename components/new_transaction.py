from datetime import datetime
import database as db
import streamlit as st

from utils import parse_valor, fmt


@st.dialog("➕ Novo Registro")
def new_transaction_dialog(user_id):
    all_cats  = db.get_all_categories(user_id)
    reset_key = st.session_state.get("form_reset_counter", 0)

    col1, col2 = st.columns(2)
    with col1:
        tipo = st.selectbox(
            "Tipo *", ["saida", "entrada"],
            format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada",
            key=f"tipo_{reset_key}"
        )
    with col2:
        cats_filtered = {c["name"]: c["id"] for c in all_cats if c["type"] in (tipo, "ambos")}
        categoria_nome = st.selectbox("Categoria *", [""] + list(cats_filtered.keys()),
                                      key=f"cat_{reset_key}")

    selected_cat_id = cats_filtered.get(categoria_nome)
    desc_options    = db.get_descriptions_by_category(user_id, selected_cat_id)
    descricao_final = st.selectbox(
        "Descrição",
        options=desc_options, index=None,
        accept_new_options=True,
        placeholder="Digite ou selecione uma descrição...",
        key=f"desc_{reset_key}"
    ) or ""


    data = st.date_input("Data *", value=datetime.today(), format="DD/MM/YYYY")

    valor = st.number_input(
        "Valor Total (R$) *",
        key=f"valor_{reset_key}", placeholder="ex: R$ 1.250,00", format="%.2f", min_value=0.0)
    valor_str = str(valor)

    parcelado = st.checkbox("Parcelado?", key=f"parcelado_{reset_key}")
    parcelas  = 1
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
            st.rerun()

