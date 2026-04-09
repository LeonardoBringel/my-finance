import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.styles import (
    init_onboarding,
    inject_global_css,
    inject_subpage_css,
    page_header,
)
from repositories import CategoriesRepository
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
categories = CategoriesRepository.list_categories(user_id)

type_labels = {"entrada": "💰 Entrada", "saida": "💸 Saída", "ambos": "🔄 Ambos"}

f_type = st.selectbox(
    "Filtrar por tipo",
    ["Todos", "entrada", "saida", "ambos"],
    format_func=lambda x: "Todos" if x == "Todos" else type_labels[x],
)

if f_type != "Todos":
    categories = [c for c in categories if c["type"] == f_type]

st.markdown(f"**{len(categories)} categoria(s)**")
st.divider()

if not categories:
    st.info("Nenhuma categoria encontrada.")
else:
    header = st.columns([3, 2, 0.8, 0.8])
    for h, label in zip(header, ["Nome", "Tipo", "✏️", "🗑️"]):
        h.markdown(f"**{label}**")
    st.divider()

    for cat in categories:
        cols = st.columns([3, 2, 0.8, 0.8])
        cols[0].markdown(cat["name"])
        cols[1].markdown(type_labels.get(cat["type"], cat["type"]))

        if cols[2].button("✏️", key=f"edit_cat_{cat['id']}"):
            st.session_state[f"editing_cat_{cat['id']}"] = True

        if cols[3].button("🗑️", key=f"del_cat_{cat['id']}"):
            st.session_state["confirm_del_cat_id"] = cat["id"]
            st.session_state["confirm_del_cat_name"] = cat["name"]

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
