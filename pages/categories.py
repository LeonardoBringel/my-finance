import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.styles import (
    init_onboarding,
    inject_global_css,
    inject_subpage_css,
    page_header,
)
from repositories import CategoriesRepository, TransactionsRepository
from utils.auth import require_login

inject_global_css()

st.set_page_config(page_title="Categorias", page_icon="🏷️", layout="wide")

inject_subpage_css()

require_login()
user_id = st.session_state["current_user"]["id"]


# ── Onboarding ─────────────────────────────────────────────────────────────────
@st.dialog("🏷️ Bem-vindo às Categorias", width="large")
def onboarding_dialog():
    """Dialog de boas-vindas com instruções sobre o gerenciamento de categorias."""
    st.markdown(
        """
### O que são Categorias?

As **Categorias** organizam seus lançamentos financeiros, permitindo visualizar para onde
seu dinheiro está indo e de onde ele vem.

---

### Tipos de categoria

| Tipo | Uso |
|---|---|
| 💸 **Saída** | Despesas, contas, compras |
| 💰 **Entrada** | Salário, renda, recebimentos |
| 🔄 **Ambos** | Categorias que servem para entradas e saídas |

---

### Como começar?

1. Use o formulário **➕ Nova Categoria** para criar sua primeira categoria.
2. Dê um nome claro, como *Alimentação*, *Salário* ou *Aluguel*.
3. Escolha o tipo adequado e clique em **💾 Adicionar**.

Depois de criar as categorias, você poderá registrar lançamentos e visualizá-los
organizados no Dashboard.
    """
    )
    st.divider()
    if st.button(
        "✅ Entendido, vamos começar!", type="primary", use_container_width=True
    ):
        st.rerun()


init_onboarding("cat", not CategoriesRepository.has_any_category(user_id))
if st.session_state.pop("cat_show_onboarding", False):
    onboarding_dialog()

page_header("🏷️ Gerenciar Categorias", cleanup_keys=["show_form", "form_reset_counter"])

st.divider()

if success_msg := st.session_state.pop("cat_success_msg", None):
    st.success(success_msg)

# ── Nova Categoria ─────────────────────────────────────────────────────────────
if "new_cat_v" not in st.session_state:
    st.session_state["new_cat_v"] = 0

_v = st.session_state["new_cat_v"]

with st.expander("➕ Nova Categoria", expanded=False):
    col1, col2, col3 = st.columns([2, 1.5, 1])
    with col1:
        new_name = st.text_input("Nome da categoria", key=f"new_cat_name_{_v}")
    with col2:
        new_type = st.selectbox(
            "Tipo",
            ["saida", "entrada", "ambos"],
            format_func=lambda x: {
                "saida": "💸 Saída",
                "entrada": "💰 Entrada",
                "ambos": "🔄 Ambos",
            }[x],
            key=f"new_cat_type_{_v}",
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Adicionar", type="primary", use_container_width=True):
            if new_name.strip():
                ok, msg = CategoriesRepository.create_category(
                    user_id, new_name.strip(), new_type
                )
                if ok:
                    st.session_state["cat_success_msg"] = msg
                    st.session_state["new_cat_v"] += 1
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error("Digite um nome para a categoria.")

# ── Lista de Categorias ────────────────────────────────────────────────────────
all_categories = CategoriesRepository.list_categories(user_id)
txn_counts = CategoriesRepository.get_transaction_counts_by_category(user_id)

type_labels = {"entrada": "💰 Entrada", "saida": "💸 Saída", "ambos": "🔄 Ambos"}

f_type = st.selectbox(
    "Filtrar por tipo",
    ["Todos", "entrada", "saida", "ambos"],
    format_func=lambda x: "Todos" if x == "Todos" else type_labels[x],
)

categories = all_categories
if f_type != "Todos":
    categories = [c for c in all_categories if c["type"] == f_type]

st.markdown(f"**{len(categories)} categoria(s)**")
st.divider()

if not categories:
    st.info("Nenhuma categoria encontrada.")
else:
    header = st.columns([2.5, 1.5, 1.5, 0.8, 0.8])
    for h, label in zip(header, ["Nome", "Tipo", "Lançamentos", "✏️", "🗑️"]):
        h.markdown(f"**{label}**")
    st.divider()

    for cat in categories:
        cols = st.columns([2.5, 1.5, 1.5, 0.8, 0.8])
        cols[0].markdown(cat["name"])
        cols[1].markdown(type_labels.get(cat["type"], cat["type"]))
        count = txn_counts.get(cat["id"], 0)
        cols[2].markdown(f"{count}")

        if cols[3].button("✏️", key=f"edit_cat_{cat['id']}"):
            st.session_state[f"editing_cat_{cat['id']}"] = True

        if cols[4].button("🗑️", key=f"del_cat_{cat['id']}"):
            st.session_state["confirm_del_cat_id"] = cat["id"]
            st.session_state["confirm_del_cat_name"] = cat["name"]

        # ── Descriptions expander ──────────────────────────────────────────────
        active_key = f"active_desc_{cat['id']}"
        descs = TransactionsRepository.get_descriptions_with_counts(user_id, cat["id"])
        is_expanded = st.session_state.get(active_key) is not None
        with st.expander(f"📋 Descrições ({len(descs)})", expanded=is_expanded):
            if not descs:
                st.info("Nenhuma descrição cadastrada para esta categoria.")
            else:
                dh = st.columns([3.5, 0.8, 0.7, 0.7])
                dh[0].markdown("**Descrição**")
                dh[1].markdown("**Qtd**")
                dh[2].markdown("**✏️**")
                dh[3].markdown("**↗️**")

                for idx, di in enumerate(descs):
                    dc = st.columns([3.5, 0.8, 0.7, 0.7])
                    dc[0].markdown(di["description"])
                    dc[1].markdown(str(di["count"]))

                    if dc[2].button("✏️", key=f"drename_{cat['id']}_{idx}"):
                        st.session_state[active_key] = {"idx": idx, "action": "rename"}
                        st.rerun()

                    if dc[3].button("↗️", key=f"dmigrate_{cat['id']}_{idx}"):
                        st.session_state[active_key] = {"idx": idx, "action": "migrate"}
                        st.rerun()

                    active = st.session_state.get(active_key)
                    if active and active["idx"] == idx:
                        if active["action"] == "rename":
                            rf1, rf2, rf3 = st.columns([3.5, 0.7, 0.7])
                            new_desc_val = rf1.text_input(
                                "Nova descrição",
                                value=di["description"],
                                key=f"rnew_{cat['id']}_{idx}",
                            )
                            rf2.markdown("<br>", unsafe_allow_html=True)
                            if rf2.button(
                                "💾", key=f"rsave_{cat['id']}_{idx}", type="primary"
                            ):
                                trimmed = new_desc_val.strip()
                                if not trimmed:
                                    st.error("Digite um nome.")
                                elif trimmed == di["description"]:
                                    st.error("Digite um nome diferente.")
                                else:
                                    updated = TransactionsRepository.rename_description(
                                        user_id, cat["id"], di["description"], trimmed
                                    )
                                    st.session_state.pop(active_key, None)
                                    st.session_state[
                                        "cat_success_msg"
                                    ] = f"{updated} transação(ões) renomeada(s)."
                                    st.rerun()
                            rf3.markdown("<br>", unsafe_allow_html=True)
                            if rf3.button("❌", key=f"rcancel_{cat['id']}_{idx}"):
                                st.session_state.pop(active_key, None)
                                st.rerun()

                        elif active["action"] == "migrate":
                            mf1, mf2, mf3, mf4 = st.columns([2, 2, 0.7, 0.7])
                            tgt_cat = mf1.selectbox(
                                "Categoria destino",
                                all_categories,
                                format_func=lambda c: c["name"],
                                key=f"mtgtcat_{cat['id']}_{idx}",
                            )
                            tgt_descs = (
                                TransactionsRepository.get_descriptions_with_counts(
                                    user_id, tgt_cat["id"]
                                )
                            )
                            tgt_desc_list = [d["description"] for d in tgt_descs]
                            if tgt_desc_list:
                                tgt_desc = mf2.selectbox(
                                    "Descrição destino",
                                    tgt_desc_list,
                                    key=f"mtgtdesc_{cat['id']}_{idx}_{tgt_cat['id']}",
                                )
                            else:
                                tgt_desc = None
                                mf2.info("Categoria sem descrições.")
                            mf3.markdown("<br>", unsafe_allow_html=True)
                            if mf3.button(
                                "💾", key=f"msave_{cat['id']}_{idx}", type="primary"
                            ):
                                if tgt_desc is None:
                                    st.error("Selecione uma descrição destino.")
                                elif (
                                    tgt_cat["id"] == cat["id"]
                                    and tgt_desc == di["description"]
                                ):
                                    st.error("Selecione um destino diferente.")
                                else:
                                    updated = (
                                        TransactionsRepository.migrate_description(
                                            user_id,
                                            cat["id"],
                                            di["description"],
                                            tgt_cat["id"],
                                            tgt_desc,
                                        )
                                    )
                                    st.session_state.pop(active_key, None)
                                    st.session_state[
                                        "cat_success_msg"
                                    ] = f"{updated} transação(ões) migrada(s)."
                                    st.rerun()
                            mf4.markdown("<br>", unsafe_allow_html=True)
                            if mf4.button("❌", key=f"mcancel_{cat['id']}_{idx}"):
                                st.session_state.pop(active_key, None)
                                st.rerun()

        if st.session_state.get(f"editing_cat_{cat['id']}"):
            with st.container():
                ec1, ec2, ec3, ec4 = st.columns([3, 2, 1, 1])
                with ec1:
                    edit_name = st.text_input(
                        "Nome", value=cat["name"], key=f"ename_{cat['id']}"
                    )
                with ec2:
                    edit_type = st.selectbox(
                        "Tipo",
                        ["saida", "entrada", "ambos"],
                        index=["saida", "entrada", "ambos"].index(cat["type"]),
                        format_func=lambda x: type_labels[x],
                        key=f"etype_{cat['id']}",
                    )
                with ec3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾", key=f"save_cat_{cat['id']}", type="primary"):
                        ok, msg = CategoriesRepository.update_category(
                            user_id, cat["id"], edit_name, edit_type
                        )
                        if ok:
                            st.success(msg)
                            st.session_state.pop(f"editing_cat_{cat['id']}", None)
                            st.rerun()
                        else:
                            st.error(msg)
                with ec4:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("❌", key=f"cancel_cat_{cat['id']}"):
                        st.session_state.pop(f"editing_cat_{cat['id']}", None)
                        st.rerun()

        if st.session_state.get("confirm_del_cat_id") == cat["id"]:
            st.warning(f"⚠️ Excluir categoria **{cat['name']}**?")
            cc1, cc2, _ = st.columns([1, 1, 4])
            if cc1.button("✅ Confirmar", key=f"conf_cat_{cat['id']}", type="primary"):
                CategoriesRepository.delete_category(user_id, cat["id"])
                st.session_state.pop("confirm_del_cat_id", None)
                st.session_state.pop("confirm_del_cat_name", None)
                st.rerun()
            if cc2.button("❌ Cancelar", key=f"canc_cat_{cat['id']}"):
                st.session_state.pop("confirm_del_cat_id", None)
                st.session_state.pop("confirm_del_cat_name", None)
                st.rerun()
